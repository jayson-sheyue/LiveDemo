"""Generate short WAV samples with macOS `say` + `afconvert`. Offline, no Google."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / 'sample_assets' / 'audio'
ASSETS = ROOT / 'sample_assets'

MANDARIN_SYSTEM = (
    'You are a concise voice assistant. '
    'RESPOND IN MANDARIN. YOU MUST RESPOND UNMISTAKABLY IN 普通话。'
    '用口语化的短句回答。'
)
ENGLISH_SYSTEM = (
    'You are a concise voice assistant. Speak English. '
    'Keep replies to one or two short spoken sentences.'
)
JA_SYSTEM = (
    'You are a concise voice assistant. '
    'RESPOND IN JAPANESE. YOU MUST RESPOND UNMISTAKABLY IN 日本語。'
    '短い口語で答えてください。'
)


def say_wav(text: str, voice: str, dest: Path, rate: int = 16000) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        aiff = Path(tmp) / 'clip.aiff'
        subprocess.run(['say', '-v', voice, '-o', str(aiff), text], check=True)
        subprocess.run(
            ['afconvert', '-f', 'WAVE', '-d', f'LEI16@{rate}', str(aiff), str(dest)],
            check=True,
        )


def sample(id_, title, group, note, engine, expected, audio=None, **config):
    item = {
        'id': id_,
        'title': title,
        'group': group,
        'note': note,
        'engine': engine,
        'expected': expected,
        'config': config,
    }
    if audio:
        item['audio'] = audio
    return item


def write_json(item: dict, filename: str) -> None:
    (ASSETS / filename).write_text(json.dumps(item, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> None:
    rows = [
        sample(
            'talk-cmn', '入门 · 普通话打招呼', '先这样开口',
            '语言选「不指定」。普通话写在系统指令里，因为 Live SpeechConfig 官方表没有 cmn-Hans-CN。',
            'talk', '你好，我是语音助手。',
            voice='Kore', language='', input_transcript=True, output_transcript=True,
            system_instruction=MANDARIN_SYSTEM,
        ),
        sample(
            'talk-en', '对照 · English concierge', '先这样开口',
            '同一套原生音频模型，SpeechConfig.language_code=en-US，系统指令改成英语。',
            'talk', 'Hi, how can I help?',
            voice='Puck', language='en-US', input_transcript=True, output_transcript=True,
            system_instruction=ENGLISH_SYSTEM,
        ),
        sample(
            'talk-barge', '功能 · 打断', '先这样开口',
            '让它开始说话后立刻再开口。服务端 VAD 会发 interrupted，本地播放应停下。戴耳机更不容易把自己的声音当成打断。',
            'talk', '（说一半被打断）',
            voice='Fenrir', language='', input_transcript=True, output_transcript=True, barge_in=True,
            system_instruction=MANDARIN_SYSTEM + '先用两三句比较长的话回答，方便练习打断。',
        ),
        sample(
            'talk-ja', '对照 · 日本語', '先这样开口',
            '官方语言表有 ja-JP。可以同时在系统指令里再钉一次日语。',
            'talk', 'こんにちは。',
            voice='Aoede', language='ja-JP', input_transcript=True, output_transcript=True,
            system_instruction=JA_SYSTEM,
        ),
        sample(
            'talk-video', '功能 · 摄像头', '先这样开口',
            '勾选打开摄像头。官方把视频当成 JPEG，最多 1 帧/秒。无压缩时音视频会话大约 2 分钟。模型不会回传画面，只会看着说。',
            'talk', '我看见……',
            voice='Kore', language='', input_transcript=True, output_transcript=True,
            video=True, barge_in=True,
            system_instruction=MANDARIN_SYSTEM + '根据摄像头画面，用一两句普通话描述你看见的东西。',
        ),
        sample(
            'talk-screen', '功能 · 屏幕共享', '先这样开口',
            '勾选共享屏幕。同样是 JPEG 1 帧/秒，不是双向投屏。若同时打开摄像头，会合成一张画中画（屏幕大图、摄像头小窗）再发出去。',
            'talk', '屏幕上是……',
            voice='Kore', language='', input_transcript=True, output_transcript=True,
            screen=True, barge_in=True, session_resume=True,
            system_instruction=MANDARIN_SYSTEM + '根据共享屏幕，用一两句普通话描述你看见的内容。',
        ),
        sample(
            'talk-pip', '功能 · 画中画', '先这样开口',
            '同时打开摄像头和屏幕。官方只有一条 JPEG 流，Demo 把两路合成一张：屏幕是底图，摄像头在右下角小窗，仍是 1 帧/秒。',
            'talk', '屏幕上是……角落里是我。',
            voice='Kore', language='', input_transcript=True, output_transcript=True,
            video=True, screen=True, barge_in=True, session_resume=True,
            system_instruction=MANDARIN_SYSTEM + '画面是画中画：大图是屏幕，右下角小窗是摄像头。分别用短句说明两边看见什么。',
        ),
        sample(
            'talk-tools', '功能 · 演示函数', '先这样开口',
            '问「现在几点了」。服务端会执行 get_current_time，再把结果说给你听。不能和 Google 搜索同时开。',
            'talk', '现在是……',
            voice='Kore', language='', input_transcript=True, output_transcript=True,
            tools='demo', barge_in=True, session_resume=True,
            system_instruction=MANDARIN_SYSTEM + '用户问时间或实验室状态时，必须调用对应工具，再用口语转述结果。',
        ),
        sample(
            'talk-search', '功能 · Google 搜索', '先这样开口',
            '问一个需要上网的事实问题。这是官方 google_search 接地，不是自定义函数。',
            'talk', '（根据网页简短回答）',
            voice='Kore', language='', input_transcript=True, output_transcript=True,
            tools='search', barge_in=True, session_resume=True,
            system_instruction=MANDARIN_SYSTEM + '需要事实时使用 Google 搜索。用一两句口语回答，不要念网址。',
        ),
        sample(
            'talk-native', '功能 · 情感 / 主动音频', '先这样开口',
            'Affective Dialog + Proactive Audio 都是 Preview。闲聊或背景声它可能不接话；被明确提问时才开口。官方提示情感模式可能出意外效果。',
            'talk', '（相关话题才接话）',
            voice='Kore', language='', input_transcript=True, output_transcript=True,
            affective=True, proactive=True, barge_in=True, session_resume=True,
            system_instruction=MANDARIN_SYSTEM + '只有被明确提问时才开口。闲聊、自言自语和背景声保持沉默。',
        ),
        sample(
            'talk-compress', '功能 · 上下文压缩', '先这样开口',
            '打开摄像头并勾选上下文压缩。无压缩时音视频大约 2 分钟；压缩用滑动窗口裁旧轮次，可把会话拉长。',
            'talk', '（长会话仍能接话）',
            voice='Kore', language='', input_transcript=True, output_transcript=True,
            video=True, compress=True, barge_in=True, session_resume=True,
            system_instruction=MANDARIN_SYSTEM,
        ),
        sample(
            'cap-cmn', '入门 · 普通话', '对着麦说',
            '点开始听写，对着麦克风说话。模型是 gemini-3.5-transcribe-live-preview，区域 global。',
            'transcribe', '对着麦克风说普通话。',
            language='cmn-Hans-CN',
        ),
        sample(
            'cap-en', '对照 · English', '对着麦说',
            '同一条 Live 听写，换 locale。这不是 Chirp 3。',
            'transcribe', 'Speak English into the mic.',
            language='en-US',
        ),
        sample(
            'cap-auto', '功能 · 自动检测语言', '对着麦说',
            'language_codes 不发送。官方：85+ 语言自动检测，含会话中夹杂。',
            'transcribe', '随便说一种语言，看它是否检测。',
            language='auto',
        ),
        sample(
            'cap-vocab', '功能 · 自定义词表', '对着麦说',
            '词表只放专有名词。对着麦说项目代号 webeye-internal-test。',
            'transcribe', '请说：项目代号 webeye-internal-test。',
            language='cmn-Hans-CN', vocabulary='webeye-internal-test',
        ),
        sample(
            'cap-ja', '对照 · 日本語', '对着麦说',
            'ja-JP 在 3.5 Transcribe 语言表是 Supported。',
            'transcribe', 'マイクに向かって日本語で話してください。',
            language='ja-JP',
        ),
        sample(
            'say-cmn', '入门 · 请用普通话自我介绍', '先听它说',
            '不需要麦克风。仍是 Live 会话，不是 Cloud TTS。系统指令钉普通话。',
            'textturn', '（模型用普通话做一句自我介绍）',
            voice='Kore', language='', text='请用一句话介绍你自己，说明你是语音助手。',
            system_instruction=MANDARIN_SYSTEM, output_transcript=True,
        ),
        sample(
            'say-en', '对照 · Say hello', '先听它说',
            '换英语指令和 Puck。对照中文那条听音色和语言。',
            'textturn', 'Hello, I am a voice assistant.',
            voice='Puck', language='en-US', text='Introduce yourself in one short spoken sentence.',
            system_instruction=ENGLISH_SYSTEM, output_transcript=True,
        ),
        sample(
            'say-ja', '对照 · 日本語で', '先听它说',
            'language_code=ja-JP，系统指令再钉日语。',
            'textturn', 'こんにちは。',
            voice='Aoede', language='ja-JP', text='日本語で、短く自己紹介してください。',
            system_instruction=JA_SYSTEM, output_transcript=True,
        ),
        sample(
            'say-video', '功能 · 看见图', '先听它说',
            '勾选摄像头。打字页没有麦克风，所以没有打断。会话开着按约 1 帧/秒推 JPEG，不是一张静图。模型不回传画面。',
            'textturn', '（根据画面用普通话短说一句）',
            voice='Kore', language='', video=True, output_transcript=True, session_resume=True,
            text='请根据画面，用一句话描述你看见了什么。',
            system_instruction=MANDARIN_SYSTEM + '根据画面描述，不要编造摄像头里没有的东西。',
        ),
        sample(
            'say-tools', '功能 · 现在几点', '先听它说',
            '打字问现在几点。同一条长连接，走演示函数 get_current_time。',
            'textturn', '现在是……',
            voice='Kore', language='', tools='demo', output_transcript=True, session_resume=True,
            text='现在几点了？请调用工具后用一句话告诉我。',
            system_instruction=MANDARIN_SYSTEM + '用户问时间时必须调用 get_current_time。',
        ),
    ]
    names = []
    for index, item in enumerate(rows, start=1):
        filename = f'{index:02d}_{item["id"]}.json'
        write_json(item, filename)
        names.append(filename)
    (ASSETS / 'index.json').write_text(json.dumps({'samples': names}, indent=2) + '\n', encoding='utf-8')
    print(f'{len(names)} samples')


if __name__ == '__main__':
    main()
