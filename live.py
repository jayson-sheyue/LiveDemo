"""Gemini Live API adapters. Preview does not call Google."""
from __future__ import annotations

import asyncio
import base64
import io
import os
import re
import traceback
import wave
from datetime import datetime
from typing import Any, AsyncIterator, Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from catalog import (
    ENGINE_LOCATIONS, INPUT_RATE, MODEL_TALK, MODEL_TRANSCRIBE, MODELS, NATIVE_REGIONS,
    OUTPUT_RATE, VOICE_NAMES, WORKSPACES,
)

MAX_AUDIO_BYTES = 8_000_000
MAX_VIDEO_BYTES = 400_000
MAX_VOCAB = 100
COMPRESS_TRIGGER = 50_000
COMPRESS_TARGET = 25_000
DEMO_TOOLS = [
    {
        'name': 'get_current_time',
        'description': '返回当前时间。用户问现在几点、今天几号时调用。',
    },
    {
        'name': 'get_lab_status',
        'description': '返回这个本地教学 Demo 是否在运行。不是生产监控，不要当成真实运维接口。',
    },
]
WORKSPACE_INDEX = {item['id']: item for item in WORKSPACES}
_PROXY_CONFIGURED = False
_PROXY_NOTES: list[str] = []


def configure_live_proxy() -> list[str]:
    """macOS 系统代理常把 Clash 暴露成 SOCKS。websockets 会优先走 SOCKS，没装 python-socks 就连不上。

    若同时有 HTTP 代理（Clash 7890 通常 HTTP/SOCKS 同端口），改走 HTTP CONNECT。
    """
    global _PROXY_CONFIGURED, _PROXY_NOTES
    if _PROXY_CONFIGURED:
        return list(_PROXY_NOTES)
    _PROXY_CONFIGURED = True
    try:
        import urllib.request
        proxies = urllib.request.getproxies()
    except Exception:
        return []
    if not proxies.get('socks'):
        return []
    if os.environ.get('https_proxy') or os.environ.get('HTTPS_PROXY'):
        return []
    http = proxies.get('https') or proxies.get('http')
    if not http:
        _PROXY_NOTES = ['本机开了 SOCKS 代理。请安装 python-socks，或在 Clash 打开 HTTP 代理后重启 Demo。']
        return list(_PROXY_NOTES)
    if not http.startswith(('http://', 'https://', 'socks5://', 'socks5h://')):
        http = 'http://' + http
    os.environ['https_proxy'] = http
    os.environ['HTTPS_PROXY'] = http
    os.environ.setdefault('http_proxy', http)
    os.environ.setdefault('HTTP_PROXY', http)
    for key in ('no_proxy', 'NO_PROXY'):
        current = os.environ.get(key, '')
        extra = '127.0.0.1,localhost'
        if extra not in current:
            os.environ[key] = f'{current},{extra}'.strip(',')
    try:
        import urllib.request
        cache_clear = getattr(urllib.request.getproxies, 'cache_clear', None)
        if callable(cache_clear):
            cache_clear()
    except Exception:
        pass
    _PROXY_NOTES = [f'本机系统代理含 SOCKS。Live WebSocket 已改走 HTTP 代理 {http}。']
    return list(_PROXY_NOTES)


class UserError(ValueError):
    pass


class Request(BaseModel):
    engine: Literal['talk', 'transcribe', 'textturn'] = 'talk'
    model: str = MODEL_TALK
    voice: str = 'Kore'
    language: str = Field(default='', max_length=32)
    languages: str = Field(default='', max_length=400)
    system_instruction: str = Field(default='', max_length=4000)
    text: str = Field(default='', max_length=4000)
    sample_id: str = Field(default='', max_length=80)
    audio_b64: str = Field(default='', max_length=12_000_000)
    filename: str = Field(default='', max_length=200)
    input_transcript: bool = True
    output_transcript: bool = True
    vocabulary: str = Field(default='', max_length=2000)
    location: str = Field(default='', max_length=32)
    barge_in: bool = True
    video: bool = False
    screen: bool = False
    session_resume: bool = False
    resume_handle: str = Field(default='', max_length=8000)
    compress: bool = False
    affective: bool = False
    proactive: bool = False
    tools: str = Field(default='', max_length=16)
    video_frames: list[str] = Field(default_factory=list, max_length=3)


def adc_available() -> bool:
    try:
        import google.auth
        credentials, _project = google.auth.default()
        return credentials is not None
    except Exception:
        return False


def require_auth() -> None:
    if not (os.getenv('GOOGLE_CLOUD_PROJECT') or '').strip():
        raise UserError('请在 .env 填写 GOOGLE_CLOUD_PROJECT，并运行：gcloud auth application-default login。预览无需凭据。')
    if not adc_available():
        raise UserError('未检测到 Application Default Credentials。请运行：gcloud auth application-default login，然后 gcloud auth application-default set-quota-project 你的项目ID，并重启服务。')


def workspace(engine: str) -> dict:
    spec = WORKSPACE_INDEX.get(engine)
    if not spec:
        raise UserError('未知工作台。')
    return spec


def phrases(raw: str) -> list[str]:
    items = []
    for part in re.split(r'[\n,，;；]+', raw or ''):
        text = part.strip()
        if text and text not in items:
            items.append(text[:80])
        if len(items) >= MAX_VOCAB:
            break
    return items


def transcribe_languages(r: Request) -> list[str]:
    primary = (r.language or '').strip()
    extras = []
    for part in re.split(r'[\n,，;；]+', r.languages or ''):
        text = part.strip()
        if text and text not in extras:
            extras.append(text)
    codes = []
    for item in [primary] + extras:
        if item and item not in codes:
            codes.append(item)
    if 'auto' in codes:
        if len(codes) > 1:
            raise UserError('自动检测不能和具体 locale 写在一起。请只选 auto，或只选具体语言。')
        return []
    return codes


def location_for(r: Request) -> tuple[str, list[str]]:
    spec = workspace(r.engine)
    default = ENGINE_LOCATIONS[spec['id']]
    raw = (r.location or os.getenv('GOOGLE_CLOUD_LOCATION') or '').strip()
    warnings: list[str] = []
    if r.engine == 'transcribe':
        if raw and raw != 'global':
            warnings.append(f'Transcribe Live 官方区域是 global，已把 {raw} 改成 global。')
        return 'global', warnings
    if raw == 'global' or not raw:
        if raw == 'global':
            warnings.append('原生音频 Live 是区域接口。已把 global 改成 us-central1。那是 TTS 常用区域，不是这一页的。')
        return default, warnings
    if raw not in NATIVE_REGIONS:
        warnings.append(f'区域 {raw} 不在本 Demo 白名单，已改用 {default}。请以模型卡为准。')
        return default, warnings
    return raw, warnings


def wav_info(data: bytes) -> tuple[int, int, int] | None:
    if len(data) < 44 or data[:4] != b'RIFF' or data[8:12] != b'WAVE':
        return None
    try:
        with wave.open(io.BytesIO(data), 'rb') as handle:
            return handle.getnchannels(), handle.getsampwidth(), handle.getframerate()
    except wave.Error:
        return None


def pcm16_mono(data: bytes, expected_rate: int = INPUT_RATE) -> bytes:
    info = wav_info(data)
    if not info:
        if data[:4] == b'RIFF':
            raise UserError('无法读取这段 WAV。请换成 16 kHz 单声道 16-bit PCM。')
        return data
    channels, width, rate = info
    if channels != 1 or width != 2:
        raise UserError('Live 输入需要单声道 16-bit PCM。请用工作台录音，或上传 16 kHz 单声道 WAV。')
    if rate != expected_rate:
        raise UserError(f'Live 输入采样率需要 {expected_rate} Hz，这段音频是 {rate} Hz。')
    with wave.open(io.BytesIO(data), 'rb') as handle:
        return handle.readframes(handle.getnframes())


def encode_wav(pcm: bytes, rate: int = OUTPUT_RATE) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(pcm)
    return buffer.getvalue()


def decode_audio(r: Request) -> bytes:
    raw = (r.audio_b64 or '').strip()
    if not raw:
        raise UserError('请先点一个带音频的样例、上传 WAV 或录音。')
    try:
        data = base64.b64decode(raw, validate=False)
    except Exception as error:
        raise UserError('音频不是合法的 Base64。') from error
    if len(data) > MAX_AUDIO_BYTES:
        raise UserError('音频过大。请使用短于约 1 分钟的片段。')
    if not data:
        raise UserError('音频是空的。')
    return data


def validate(r: Request) -> None:
    spec = workspace(r.engine)
    allowed = MODELS[spec['id']]
    if r.model not in allowed:
        raise UserError(f'{spec["nav"]} 页只能用 {allowed[0]}。样例和模型不能跨页。')
    if r.engine != 'transcribe' and r.voice not in VOICE_NAMES:
        raise UserError('请选择列表中的预置声音。')
    if r.engine != 'transcribe' and r.language in {'cmn-Hans-CN', 'zh-CN', 'zh', 'cmn'}:
        raise UserError(
            '对话/打字页的 SpeechConfig.language_code 官方表没有普通话。'
            '请把语言设为「不指定」，在系统指令里写：必须用普通话回答。听写页才填 cmn-Hans-CN。'
        )
    if r.engine == 'textturn' and not (r.text or '').strip():
        raise UserError('请输入要发给模型的文字。')
    if r.engine == 'transcribe' and r.model != MODEL_TRANSCRIBE:
        raise UserError('听写页只能用 gemini-3.5-transcribe-live-preview。')
    if r.engine != 'transcribe' and r.model != MODEL_TALK:
        raise UserError('对话/打字页只能用 gemini-live-2.5-flash-native-audio。')
    if (r.video or r.screen) and r.engine not in {'talk', 'textturn'}:
        raise UserError('摄像头和屏幕共享只在对话页和打字页。Live 收 JPEG 帧，不会回传画面。')
    if r.tools and r.tools not in {'demo', 'search'}:
        raise UserError('工具只能选演示函数或 Google 搜索接地。官方不允许把搜索工具和自定义函数写在同一次 setup 里。')
    if r.tools and r.engine == 'transcribe':
        raise UserError('听写页只出字幕，不接函数调用或搜索接地。')
    if (r.affective or r.proactive) and r.engine != 'talk':
        raise UserError('Affective Dialog / Proactive Audio 是原生音频能力，只在对话页。')
    if r.resume_handle and not r.session_resume:
        raise UserError('要接着上次聊，请打开会话恢复。')
    if r.video_frames:
        if r.engine != 'textturn':
            raise UserError('抓拍帧只用于打字页。对话页是实时 1 帧/秒。')
        r.video = True
        if len(r.video_frames) > 3:
            raise UserError('最多 3 帧 JPEG。')
        for frame in r.video_frames:
            if len(frame) > 800_000:
                raise UserError('某一帧过大。请降低分辨率后再试。')


def system_text(r: Request) -> str:
    text = (r.system_instruction or '').strip()
    if text:
        return text
    if r.engine == 'transcribe':
        return ''
    if not r.language:
        return (
            'You are a concise voice assistant. '
            'RESPOND IN MANDARIN. YOU MUST RESPOND UNMISTAKABLY IN 普通话。'
            '用口语化的短句回答。'
        )
    return 'You are a concise voice assistant. Keep spoken replies short.'


def connect_payload(r: Request) -> dict[str, Any]:
    """JSON-shaped LiveConnectConfig for preview. No google-genai import."""
    if r.engine == 'transcribe':
        transcription: dict[str, Any] = {}
        codes = transcribe_languages(r)
        if codes:
            transcription['language_codes'] = codes
        vocab = phrases(r.vocabulary)
        if vocab:
            transcription['custom_vocabulary'] = vocab
        payload = {
            'response_modalities': ['TEXT'],
            'input_audio_transcription': transcription,
        }
        payload.update(session_options_payload(r))
        return payload
    payload: dict[str, Any] = {
        'response_modalities': ['AUDIO'],
        'speech_config': {
            'voice_config': {'prebuilt_voice_config': {'voice_name': r.voice}},
        },
        'system_instruction': {'parts': [{'text': system_text(r)}]},
    }
    if r.language:
        payload['speech_config']['language_code'] = r.language
    if r.input_transcript:
        payload['input_audio_transcription'] = {}
    if r.output_transcript:
        payload['output_audio_transcription'] = {}
    if r.engine == 'talk':
        payload['realtime_input_config'] = {
            'activity_handling': (
                'START_OF_ACTIVITY_INTERRUPTS' if r.barge_in else 'NO_INTERRUPTION'
            ),
        }
    payload.update(session_options_payload(r))
    return payload


def session_options_payload(r: Request) -> dict[str, Any]:
    extra: dict[str, Any] = {}
    if r.session_resume:
        handle = (r.resume_handle or '').strip()
        extra['session_resumption'] = {'handle': handle} if handle else {}
    if r.compress:
        extra['context_window_compression'] = {
            'trigger_tokens': COMPRESS_TRIGGER,
            'sliding_window': {'target_tokens': COMPRESS_TARGET},
        }
    if r.engine == 'transcribe':
        return extra
    if r.affective:
        extra['enable_affective_dialog'] = True
    if r.proactive:
        extra['proactivity'] = {'proactive_audio': True}
    if r.tools == 'demo':
        extra['tools'] = [{'function_declarations': DEMO_TOOLS}]
    elif r.tools == 'search':
        extra['tools'] = [{'google_search': {}}]
    return extra


def plan(r: Request, audio: bytes | None = None) -> dict[str, Any]:
    validate(r)
    location, warnings = location_for(r)
    spec = workspace(r.engine)
    if audio:
        info = wav_info(audio)
        if info:
            channels, width, rate = info
            if channels != 1 or width != 2 or rate != INPUT_RATE:
                warnings.append(f'这段 WAV 是 {channels} 声道 / {width * 8}-bit / {rate} Hz。Live 输入要单声道 16-bit {INPUT_RATE} Hz。')
        elif audio[:4] == b'RIFF':
            warnings.append('无法解析 WAV 头。发送前会再检查一次。')
    if r.engine != 'transcribe' and not r.language:
        warnings.append('未指定 SpeechConfig.language_code。普通话靠系统指令钉语言，这是官方表里没有 cmn-Hans-CN 时的做法。')
    if r.engine == 'transcribe':
        warnings.append('这是 Gemini 3.5 Transcribe Live（Preview），不是 Chirp 3 StreamingRecognize。')
    if r.engine == 'talk' and r.barge_in:
        warnings.append('已打开打断：服务端 VAD 检测到你开口会发 interrupted，本地应立刻停播。戴耳机更稳。开关在开始会话前生效。')
    if r.engine == 'talk' and not r.barge_in:
        warnings.append('已关闭打断：它说话时 Demo 不把麦克风送回云端。要改开关请先停止再开始。')
    if r.engine in {'talk', 'textturn'} and r.video and r.screen:
        warnings.append('摄像头和屏幕会合成一张画中画 JPEG（屏幕是大图，摄像头在小窗），仍按最多 1 帧/秒发送。官方没有双路视频。')
    elif r.engine in {'talk', 'textturn'} and (r.video or r.screen):
        kind = '屏幕共享' if r.screen else '摄像头'
        warnings.append(f'{kind}按官方约定发 JPEG，最多 1 帧/秒。无压缩时音视频大约 2 分钟；勾选上下文压缩可拉长。模型只看不回传画面。')
    if r.session_resume:
        warnings.append('已打开会话恢复。服务会下发 handle；约 10 分钟 goAway 后可用「接着上次」重连，句柄大约 24 小时内有效。')
        if r.resume_handle:
            warnings.append('正在用上次的恢复句柄重连，上下文会接到上一根线。')
    if r.compress:
        warnings.append(f'已打开上下文压缩：超过约 {COMPRESS_TRIGGER} token 会滑动窗口收到约 {COMPRESS_TARGET}。旧轮次可能被裁掉。')
    if r.affective:
        warnings.append('Affective Dialog 已开（Preview）：它会按你的语气调整回答，官方提示可能出现意外效果。')
    if r.proactive:
        warnings.append('Proactive Audio 已开（Preview）：无关话题或背景声它可能不接话。输入音频仍计费。')
    if r.tools == 'demo':
        warnings.append('已接教学函数 get_current_time / get_lab_status。问「现在几点」可看到工具调用。')
    if r.tools == 'search':
        warnings.append('已打开 Google 搜索接地。不要和自定义函数同时开。回答会参考网页，不一定出引用卡片。')
    host = 'aiplatform.googleapis.com' if location == 'global' else f'{location}-aiplatform.googleapis.com'
    setup = connect_payload(r)
    return {
        'api': 'live',
        'engine': r.engine,
        'model': r.model,
        'location': location,
        'voice': r.voice if r.engine != 'transcribe' else '',
        'language_codes': transcribe_languages(r) if r.engine == 'transcribe' else ([r.language] if r.language else []),
        'input_rate': INPUT_RATE,
        'output_rate': OUTPUT_RATE,
        'warnings': warnings,
        'nav': spec['nav'],
        'endpoint': f'wss://{host}/ws/google.cloud.aiplatform.v1.LlmBidiService/BidiGenerateContent',
        'request': {
            'model': r.model,
            'location': location,
            'setup': setup,
        },
    }


def live_client(location: str):
    from google import genai
    configure_live_proxy()
    require_auth()
    return genai.Client(
        vertexai=True,
        project=os.getenv('GOOGLE_CLOUD_PROJECT'),
        location=location,
    )


def live_connect_config(r: Request):
    from google.genai import types
    setup = connect_payload(r)
    kwargs: dict[str, Any] = {
        'response_modalities': setup['response_modalities'],
    }
    if r.engine == 'transcribe':
        transcription = setup.get('input_audio_transcription') or {}
        audio_kwargs: dict[str, Any] = {}
        if transcription.get('language_codes'):
            audio_kwargs['language_codes'] = transcription['language_codes']
        if transcription.get('custom_vocabulary'):
            audio_kwargs['custom_vocabulary'] = transcription['custom_vocabulary']
        kwargs['input_audio_transcription'] = types.AudioTranscriptionConfig(**audio_kwargs)
        apply_session_options(kwargs, r, types)
        return types.LiveConnectConfig(**kwargs)
    instruction = system_text(r)
    kwargs['system_instruction'] = types.Content(parts=[types.Part(text=instruction)])
    speech_kwargs: dict[str, Any] = {
        'voice_config': types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=r.voice)
        ),
    }
    if r.language:
        speech_kwargs['language_code'] = r.language
    kwargs['speech_config'] = types.SpeechConfig(**speech_kwargs)
    if r.input_transcript:
        kwargs['input_audio_transcription'] = types.AudioTranscriptionConfig()
    if r.output_transcript:
        kwargs['output_audio_transcription'] = types.AudioTranscriptionConfig()
    ric = setup.get('realtime_input_config') or {}
    if ric:
        ric_kwargs: dict[str, Any] = {}
        if ric.get('activity_handling'):
            ric_kwargs['activity_handling'] = ric['activity_handling']
        if ric_kwargs:
            kwargs['realtime_input_config'] = types.RealtimeInputConfig(**ric_kwargs)
    apply_session_options(kwargs, r, types)
    return types.LiveConnectConfig(**kwargs)


def apply_session_options(kwargs: dict[str, Any], r: Request, types) -> None:
    if r.session_resume:
        handle = (r.resume_handle or '').strip() or None
        kwargs['session_resumption'] = types.SessionResumptionConfig(handle=handle)
    if r.compress:
        kwargs['context_window_compression'] = types.ContextWindowCompressionConfig(
            trigger_tokens=COMPRESS_TRIGGER,
            sliding_window=types.SlidingWindow(target_tokens=COMPRESS_TARGET),
        )
    if r.engine == 'transcribe':
        return
    if r.affective:
        kwargs['enable_affective_dialog'] = True
    if r.proactive:
        kwargs['proactivity'] = types.ProactivityConfig(proactive_audio=True)
    if r.tools == 'demo':
        kwargs['tools'] = [{'function_declarations': DEMO_TOOLS}]
    elif r.tools == 'search':
        kwargs['tools'] = [{'google_search': {}}]


def _part_audio(part) -> bytes:
    inline = getattr(part, 'inline_data', None)
    if inline is None:
        return b''
    data = getattr(inline, 'data', None)
    return data or b''


def _text_of(value) -> str:
    if value is None:
        return ''
    if isinstance(value, str):
        return value
    return getattr(value, 'text', None) or ''


def parse_live_message(message) -> dict[str, Any]:
    event: dict[str, Any] = {}
    if getattr(message, 'setup_complete', None):
        event['setup_complete'] = True
    go_away = getattr(message, 'go_away', None)
    if go_away is not None:
        event['go_away'] = str(getattr(go_away, 'time_left', '') or 'soon')
    data = getattr(message, 'data', None)
    if data:
        event['audio'] = data if isinstance(data, bytes) else bytes(data)
    tool_call = getattr(message, 'tool_call', None)
    if tool_call is not None:
        calls = []
        for item in getattr(tool_call, 'function_calls', None) or []:
            args = getattr(item, 'args', None) or {}
            if hasattr(args, 'items'):
                args = dict(args)
            calls.append({
                'id': getattr(item, 'id', None) or '',
                'name': getattr(item, 'name', '') or '',
                'args': args,
            })
        if calls:
            event['function_calls'] = calls
    update = getattr(message, 'session_resumption_update', None)
    if update is not None:
        event['resume_handle'] = getattr(update, 'new_handle', None) or ''
        event['resumable'] = bool(getattr(update, 'resumable', False))
    sc = getattr(message, 'server_content', None)
    if not sc:
        return event
    if getattr(sc, 'interrupted', False):
        event['interrupted'] = True
    if getattr(sc, 'turn_complete', False):
        event['turn_complete'] = True
    if getattr(sc, 'generation_complete', False):
        event['generation_complete'] = True
    turn = getattr(sc, 'model_turn', None)
    parts = getattr(turn, 'parts', None) if turn else None
    audio_chunks = []
    texts = []
    if parts:
        for part in parts:
            chunk = _part_audio(part)
            if chunk:
                audio_chunks.append(chunk)
            text = getattr(part, 'text', None)
            if text:
                texts.append(text)
    # message.data 和 inline_data 经常是同一段 PCM。拼在一起会变成回音。
    if audio_chunks and 'audio' not in event:
        event['audio'] = b''.join(audio_chunks)
    if texts:
        event['model_text'] = ''.join(texts)
    interim = _text_of(getattr(sc, 'interim_input_transcription', None))
    if interim:
        event['input_transcript'] = interim
        event['input_final'] = False
    final_in = _text_of(getattr(sc, 'input_transcription', None))
    if final_in:
        event['input_transcript'] = final_in
        event['input_final'] = True
    out = _text_of(getattr(sc, 'output_transcription', None))
    if out:
        event['output_transcript'] = out
    return event


def error_payload(error: Exception) -> dict:
    raw = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
    return {
        'message': error_message(error),
        'detail': raw.strip() or type(error).__name__,
        'error_type': type(error).__name__,
    }


def error_message(error: Exception) -> str:
    if isinstance(error, UserError):
        return str(error)
    msg = str(error).lower()
    if 'socks' in msg or 'python-socks' in msg:
        return (
            '本机开了 SOCKS 代理（常见于 Clash :7890），Live 的 WebSocket 连不上。'
            '请重启 Demo：启动时会改走同一端口的 HTTP 代理。若仍失败，确认 Clash 已允许终端 / Python。'
        )
    if any(item in msg for item in ('429', 'resource_exhausted', 'quota')):
        return '请求过于频繁或额度不足（429）。请检查配额/账单，稍后再试。'
    if any(item in msg for item in ('401', '403', 'permission', 'credential', 'adc', 'reauth', 'unauthenticated')):
        return '身份验证或权限失败。请检查 ADC、GOOGLE_CLOUD_PROJECT、已启用 aiplatform.googleapis.com、账单和 IAM。'
    if '404' in msg or 'not_found' in msg:
        return '模型或区域不可用（404）。对话页用 us-central1；听写页必须 global。不要抄 TTS 的 global 去打原生音频。'
    if 'turn_coverage' in msg or ('realtime_input_config' in msg and 'invalid' in msg):
        return 'Vertex 不接受这个 realtime_input_config。摄像头仍可发 JPEG，不必设 turn_coverage。请刷新页面后重试。'
    if 'response modality' in msg or 'one response modality' in msg:
        return '会话配置不被接受：Vertex Live 同一时间只能选一种输出（对话页 AUDIO，听写页 TEXT）。字幕靠 transcription 字段，不要把 TEXT 和 AUDIO 写在一起。'
    if '1007' in msg:
        return '会话配置不被 Vertex 接受。请展开详情查看 Invalid value 字段，刷新后再试。'
    if any(item in msg for item in ('timed out', 'timeout', 'deadline', '1011', 'network is unreachable')):
        return '连接超时、中断或网络不可达。Live WebSocket 大约 10 分钟；已发出的请求仍可能计费。'
    return '会话失败，可能为服务端暂时异常或内容被拒绝。请缩短输入后重试，并参阅排错指南。'


def merge_transcript(parts: list[str]) -> str:
    acc = ''
    for part in parts:
        if not part:
            continue
        if part.startswith(acc):
            acc = part
        elif acc.startswith(part):
            continue
        else:
            acc += part
    return acc


async def send_text(session, text: str) -> None:
    from google.genai import types
    content = types.Content(role='user', parts=[types.Part(text=text)])
    await session.send_client_content(turns=[content], turn_complete=True)


async def send_pcm(session, pcm: bytes) -> None:
    from google.genai import types
    await session.send_realtime_input(
        audio=types.Blob(data=pcm, mime_type=f'audio/pcm;rate={INPUT_RATE}'),
    )


async def send_jpeg(session, raw_b64: str) -> None:
    from google.genai import types
    try:
        data = base64.b64decode(raw_b64, validate=False)
    except Exception:
        return
    if not data or len(data) > MAX_VIDEO_BYTES:
        return
    await session.send_realtime_input(
        video=types.Blob(data=data, mime_type='image/jpeg'),
    )


async def send_tool_results(session, calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from google.genai import types
    responses = []
    shown = []
    for call in calls:
        name = call.get('name') or ''
        result = run_demo_tool(name, call.get('args') or {})
        shown.append({'name': name, 'result': result})
        kwargs: dict[str, Any] = {'name': name, 'response': {'result': result}}
        if call.get('id'):
            kwargs['id'] = call['id']
        responses.append(types.FunctionResponse(**kwargs))
    if responses:
        await session.send_tool_response(function_responses=responses)
    return shown


def run_demo_tool(name: str, args: dict[str, Any]) -> str:
    if name == 'get_current_time':
        return datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')
    if name == 'get_lab_status':
        return '对话实验室本地 Demo 正在运行。这是教学用函数，不是生产监控。'
    return f'这个 Demo 没有实现工具 {name}。'


async def send_audio_end(session) -> None:
    try:
        await session.send_realtime_input(audio_stream_end=True)
    except Exception:
        pass


async def speak_turn(r: Request) -> dict[str, Any]:
    planned = plan(r)
    client = live_client(planned['location'])
    config = live_connect_config(r)
    pcm = bytearray()
    output_text: list[str] = []
    model_text: list[str] = []
    async with client.aio.live.connect(model=r.model, config=config) as session:
        for frame in r.video_frames:
            await send_jpeg(session, frame)
        if r.video_frames:
            await asyncio.sleep(0.4)
        await send_text(session, r.text.strip())
        async for message in session.receive():
            event = parse_live_message(message)
            if event.get('audio'):
                pcm.extend(event['audio'])
            if event.get('output_transcript'):
                output_text.append(event['output_transcript'])
            if event.get('model_text'):
                model_text.append(event['model_text'])
            if event.get('turn_complete') or event.get('generation_complete'):
                break
            if event.get('go_away'):
                break
    if not pcm:
        raise UserError('服务没有返回音频。请缩短文字、检查区域和声音后重试。')
    wav = encode_wav(bytes(pcm), OUTPUT_RATE)
    return {
        'audio_b64': base64.b64encode(wav).decode('ascii'),
        'sample_rate': OUTPUT_RATE,
        'transcript': merge_transcript(output_text) or merge_transcript(model_text),
        'model': r.model,
        'location': planned['location'],
        'warnings': planned['warnings'],
        'bytes': len(wav),
    }


async def iter_session_events(r: Request, incoming: AsyncIterator[bytes | dict | None]):
    planned = plan(r)
    client = live_client(planned['location'])
    config = live_connect_config(r)
    yield {'type': 'start', 'warnings': planned['warnings'], 'model': r.model, 'location': planned['location'], 'output_rate': OUTPUT_RATE}
    async with client.aio.live.connect(model=r.model, config=config) as session:
        yield {'type': 'ready'}

        async def pump_in():
            async for item in incoming:
                if item is None:
                    if r.engine == 'transcribe':
                        await send_audio_end(session)
                    break
                if isinstance(item, dict):
                    kind = item.get('type')
                    if kind == 'text' and item.get('text'):
                        await send_text(session, item['text'])
                    elif kind == 'audio_end':
                        await send_audio_end(session)
                    elif kind == 'video' and item.get('data'):
                        await send_jpeg(session, item['data'])
                    continue
                if item:
                    await send_pcm(session, item)

        async def pump_out():
            # SDK 的 receive() 在 turn_complete 后会结束生成器。对话要多轮，必须再调一次。
            while True:
                async for message in session.receive():
                    event = parse_live_message(message)
                    if not event:
                        continue
                    payload = {'type': 'event'}
                    if event.get('audio'):
                        payload['audio_b64'] = base64.b64encode(event['audio']).decode('ascii')
                    if event.get('function_calls') and r.tools == 'demo':
                        payload['function_results'] = await send_tool_results(session, event['function_calls'])
                    for key in ('input_transcript', 'input_final', 'output_transcript', 'model_text',
                                'interrupted', 'turn_complete', 'go_away', 'setup_complete',
                                'function_calls', 'resume_handle', 'resumable'):
                        if key in event:
                            payload[key] = event[key]
                    yield payload
                    if event.get('go_away'):
                        return

        out = pump_out()
        in_task = asyncio.create_task(pump_in())
        try:
            async for payload in out:
                yield payload
        finally:
            in_task.cancel()
            try:
                await in_task
            except asyncio.CancelledError:
                pass
    yield {'type': 'done'}
