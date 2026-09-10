"""Official Gemini Live API snapshot, checked 2026-09-10. No credentials here.

Talk / text-turn use gemini-live-2.5-flash-native-audio (GA, regional).
Captions use gemini-3.5-transcribe-live-preview (Preview, global).
This is Agent Platform Live API, not Cloud Speech-to-Text StreamingRecognize.
"""
from __future__ import annotations


def _doc(title, url, why):
    return {'title': title, 'url': url, 'why': why}


def _lang(code, label, stage='GA'):
    return {'code': code, 'label': label, 'stage': stage}


CHECKED = '2026-09-10'

MODEL_TALK = 'gemini-live-2.5-flash-native-audio'
MODEL_TRANSCRIBE = 'gemini-3.5-transcribe-live-preview'

ENGINE_LOCATIONS = {
    'talk': 'us-central1',
    'transcribe': 'global',
    'textturn': 'us-central1',
}
NATIVE_REGIONS = {'us-central1', 'us-east4', 'us-west1', 'europe-west4', 'asia-northeast1'}
INPUT_RATE = 16000
OUTPUT_RATE = 24000

DOC_LIVE = _doc(
    'Gemini Live API 概览',
    'https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api',
    '会话、原生音频、和 Chirp / 普通 generateContent 不是同一条路。',
)
DOC_SESSION = _doc(
    '开始并管理会话',
    'https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api/start-manage-session',
    'WebSocket 约 10 分钟、goAway、无压缩音视频约 2 分钟、输入 16 kHz / 输出 24 kHz。',
)
DOC_VOICE = _doc(
    '语言与声音',
    'https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api/configure-language-voice',
    '30 个预置声音；SpeechConfig.language_code 官方表目前没有普通话。',
)
DOC_CAP = _doc(
    'Gemini 能力（工具 / 情感对话 / 主动说话）',
    'https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api/configure-gemini-capabilities',
    '对话页可接演示函数、Google 搜索、Affective Dialog、Proactive Audio。RAG Engine 要 corpus，见入门页「网页故意没接」。',
)
DOC_TRANSCRIBE = _doc(
    'Gemini 3.5 Transcribe',
    'https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-5-transcribe',
    'Live 字幕模型 ID、global、最多约 10 分钟、不是 Chirp StreamingRecognize。',
)
DOC_ADC = _doc(
    'ADC 配置',
    'https://docs.cloud.google.com/docs/authentication/provide-credentials-adc',
    '本地登录，不要把密钥写进前端。',
)
DOC_CHIRP = _doc(
    'Chirp 3（对照，不是本 Demo）',
    'https://docs.cloud.google.com/speech-to-text/docs/models/chirp-3',
    '要 GA 听写、电话、医学、批量，请走 Speech-to-Text，不是 Live。',
)

VOICES = [
    {'name': 'Zephyr', 'style': 'Bright'},
    {'name': 'Puck', 'style': 'Upbeat'},
    {'name': 'Charon', 'style': 'Informative'},
    {'name': 'Kore', 'style': 'Firm'},
    {'name': 'Fenrir', 'style': 'Excitable'},
    {'name': 'Leda', 'style': 'Youthful'},
    {'name': 'Orus', 'style': 'Firm'},
    {'name': 'Aoede', 'style': 'Breezy'},
    {'name': 'Callirrhoe', 'style': 'Easy-going'},
    {'name': 'Autonoe', 'style': 'Bright'},
    {'name': 'Enceladus', 'style': 'Breathy'},
    {'name': 'Iapetus', 'style': 'Clear'},
    {'name': 'Umbriel', 'style': 'Easy-going'},
    {'name': 'Algieba', 'style': 'Smooth'},
    {'name': 'Despina', 'style': 'Smooth'},
    {'name': 'Erinome', 'style': 'Clear'},
    {'name': 'Algenib', 'style': 'Gravelly'},
    {'name': 'Rasalgethi', 'style': 'Informative'},
    {'name': 'Laomedeia', 'style': 'Upbeat'},
    {'name': 'Achernar', 'style': 'Soft'},
    {'name': 'Alnilam', 'style': 'Firm'},
    {'name': 'Schedar', 'style': 'Even'},
    {'name': 'Gacrux', 'style': 'Mature'},
    {'name': 'Pulcherrima', 'style': 'Forward'},
    {'name': 'Achird', 'style': 'Friendly'},
    {'name': 'Zubenelgenubi', 'style': 'Casual'},
    {'name': 'Vindemiatrix', 'style': 'Gentle'},
    {'name': 'Sadachbia', 'style': 'Lively'},
    {'name': 'Sadaltager', 'style': 'Knowledgeable'},
    {'name': 'Sulafat', 'style': 'Warm'},
]
VOICE_NAMES = [item['name'] for item in VOICES]

# Official SpeechConfig table for native-audio Live. Mandarin is not listed.
NATIVE_LANGUAGES = [
    _lang('', '不指定（用系统指令钉语言）'),
    _lang('ar-EG', '阿拉伯语（埃及）'),
    _lang('bn-BD', '孟加拉语（孟加拉）'),
    _lang('nl-NL', '荷兰语'),
    _lang('en-IN', '英语（印度）'),
    _lang('en-US', '英语（美国）'),
    _lang('fr-FR', '法语（法国）'),
    _lang('de-DE', '德语'),
    _lang('hi-IN', '印地语'),
    _lang('id-ID', '印尼语'),
    _lang('it-IT', '意大利语'),
    _lang('ja-JP', '日语'),
    _lang('ko-KR', '韩语'),
    _lang('mr-IN', '马拉地语'),
    _lang('pl-PL', '波兰语'),
    _lang('pt-BR', '葡萄牙语（巴西）'),
    _lang('ro-RO', '罗马尼亚语'),
    _lang('ru-RU', '俄语'),
    _lang('es-US', '西班牙语（美国）'),
    _lang('ta-IN', '泰米尔语'),
    _lang('te-IN', '泰卢固语'),
    _lang('th-TH', '泰语'),
    _lang('tr-TR', '土耳其语'),
    _lang('uk-UA', '乌克兰语'),
    _lang('vi-VN', '越南语'),
]

# Gemini 3.5 Transcribe: Supported rows from the official table, plus auto.
TRANSCRIBE_LANGUAGES = [
    _lang('auto', '自动检测（85+ 语言，不填 language_codes）', 'Preview'),
    _lang('cmn-Hans-CN', '普通话（简体）'),
    _lang('en-US', '英语（美国）'),
    _lang('en-GB', '英语（英国）'),
    _lang('en-IN', '英语（印度）'),
    _lang('en-AU', '英语（澳大利亚）'),
    _lang('ja-JP', '日语'),
    _lang('ko-KR', '韩语'),
    _lang('fr-FR', '法语（法国）'),
    _lang('fr-CA', '法语（加拿大）'),
    _lang('de-DE', '德语'),
    _lang('es-ES', '西班牙语（西班牙）'),
    _lang('es-US', '西班牙语（美国）'),
    _lang('pt-BR', '葡萄牙语（巴西）'),
    _lang('pt-PT', '葡萄牙语（葡萄牙）'),
    _lang('hi-IN', '印地语'),
    _lang('it-IT', '意大利语'),
    _lang('nl-NL', '荷兰语'),
    _lang('pl-PL', '波兰语'),
    _lang('ru-RU', '俄语'),
    _lang('tr-TR', '土耳其语'),
    _lang('vi-VN', '越南语'),
    _lang('uk-UA', '乌克兰语'),
    _lang('sv-SE', '瑞典语'),
    _lang('da-DK', '丹麦语'),
    _lang('fi-FI', '芬兰语'),
    _lang('el-GR', '希腊语'),
    _lang('ro-RO', '罗马尼亚语'),
    _lang('ca-ES', '加泰罗尼亚语'),
    _lang('hr-HR', '克罗地亚语'),
    _lang('yue-Hant-HK', '粤语（香港）', 'Experimental'),
    _lang('th-TH', '泰语', 'Experimental'),
    _lang('id-ID', '印尼语', 'Experimental'),
    _lang('ar-EG', '阿拉伯语（埃及）', 'Experimental'),
]

MODELS = {
    'talk': [MODEL_TALK],
    'transcribe': [MODEL_TRANSCRIBE],
    'textturn': [MODEL_TALK],
}

MODEL_CARDS = {
    MODEL_TALK: (
        '原生音频对话（GA）：麦克风进去，模型用 24 kHz PCM 说话。默认可打断（VAD / barge-in）。'
        '可选摄像头：官方把视频当成 JPEG，最多 1 帧/秒；无压缩时音视频会话大约 2 分钟。'
        '模型不回传画面。区域是 us-central1，不是 TTS 常用的 global。普通话写进系统指令。'
    ),
    MODEL_TRANSCRIBE: (
        'Gemini 3.5 Transcribe Live（Preview）：只出字幕，response_modalities=["TEXT"]。'
        '官方区域是 global，最长约 10 分钟。这不是 Cloud Speech-to-Text 的 StreamingRecognize，'
        '也不是 Chirp 3。文件转写请用同系列的 gemini-3.5-transcribe-preview（本 Demo 不接）。'
    ),
}

MODEL_RULES = [
    ['能力', 'Live 对话（本 Demo 对话页）', 'Transcribe Live（本 Demo 听写页）', 'Chirp 3 StreamingRecognize（不是本 Demo）'],
    ['产品', 'Gemini Live API / Agent Platform', 'Gemini 3.5 Transcribe · Live', 'Cloud Speech-to-Text V2'],
    ['模型阶段', 'gemini-live-2.5-flash-native-audio · GA', 'gemini-3.5-transcribe-live-preview · Preview', 'chirp_3 · GA'],
    ['你给它什么', '双向音频；可选 JPEG 1 帧/秒', '单向音频流', '单向音频流'],
    ['它给你什么', '口语回答 + 可选字幕', '字幕（interim / final）', '字幕（interim / final）'],
    ['会不会回答问题', '会，这是对话模型', '不会，只打字', '不会，只打字'],
    ['普通话', 'SpeechConfig 表没有 cmn-Hans-CN；用系统指令钉语言', '官方语言表 Supported', 'Chirp 3 语言表 GA'],
    ['电话 8 kHz / 医学 / 分轨', '不是为这些训练的', '不是 Chirp 电话/医学模型', 'telephony / medical / 1–8 轨'],
    ['会话多久', 'WSS 约 10 分钟；音频约 15 分钟；音视频约 2 分钟（无压缩）', '最多约 10 分钟', '流式连接可更长'],
    ['区域', '区域接口，默认 us-central1', 'global', 'Chirp 3：us / eu'],
    ['计费', 'Live / Gemini 价目', 'Transcribe Preview 价目', 'Speech-to-Text 价目'],
]

COMPARE_MODELS = [
    ['', '对话页', '听写页', '打字页'],
    ['模型', MODEL_TALK, MODEL_TRANSCRIBE, MODEL_TALK],
    ['阶段', 'GA', 'Preview', 'GA'],
    ['输入', '麦克风 16 kHz PCM，可选摄像头 JPEG 1fps', '麦克风 16 kHz PCM', '文本 + 可选 JPEG 1fps（同一条长连接）'],
    ['输出', '模型说话（24 kHz）+ 可选字幕', '只出文字', '模型说话（24 kHz）'],
    ['适合第一次点通', '对着麦说「你好」', '对着麦听写', '不插麦，打字后听它说；可再发一句'],
    ['区域', 'us-central1', 'global', 'us-central1'],
]

COMPARE_METHODS = [
    ['你在问什么', '实时对话', '实时字幕', '打字让它说'],
    ['人话', '像打电话：你说一句，它接一句，可以打断；开摄像头它能看见', '像开会字幕：它只打字，不插话', '还是打电话，只是你打字、它说话；点停止才挂断'],
    ['官方概念', 'Live session · AUDIO · send_realtime_input 音频', 'Live session · TEXT + input_audio_transcription', 'Live session · AUDIO · send_client_content 文本'],
    ['业务上值什么', '语音助手、接待、边走边问', '直播字幕、现场记录（生成式听写）', '无麦演示、测声音和指令、多轮打字同一条线'],
    ['本 Demo', '顶栏「对话」', '顶栏「听写」', '顶栏「打字」'],
]

COMPARE_API = [
    ['你可能听到的说法', 'GCP Live API（本 Demo）', 'Gemini API Live', 'Cloud Speech-to-Text 流式'],
    ['人话', 'Vertex / Agent Platform 上的双向 WebSocket', 'AI Studio / API Key 那条 Live', 'Chirp 的 StreamingRecognize'],
    ['鉴权', 'ADC + 项目，启用 aiplatform.googleapis.com', 'GEMINI_API_KEY', 'ADC + speech.googleapis.com'],
    ['模型 ID', 'gemini-live-2.5-flash-native-audio 等', '名称接近，入口不同', 'chirp_3'],
    ['本 Demo', '只走 Vertex + ADC', '不接，避免和 GCP 混在一个按钮里', '不接；对照见听写实验室'],
]

WHY_NOT_LIVE = [
    ['你会离开 Live，如果…', 'Live API', '去哪'],
    ['只要 GA 听写、合同级 ASR、电话/医学', '对话模型或 Preview 听写，不是 Chirp', 'Speech-to-Text / Chirp 3'],
    ['一小时会议、GCS 过夜出稿', '单段大约 10 分钟 WebSocket', 'Speech-to-Text BatchRecognize'],
    ['8 kHz 听筒、IVR、分轨客服', '输入约定是 16 kHz PCM', 'V2 telephony'],
    ['英语病历口授（仅 en-US）', '没有 medical_* 模型', 'Speech-to-Text Medical'],
    ['只要把稿子念出来，不要会话状态', 'Live 是有状态会话', 'Cloud TTS / Gemini-TTS'],
    ['离线、端侧、克隆声纹', '云端会话', '都不是这条 API'],
    ['指望 Live 万能：会议纪要 + ASR + TTS + 双向视频', '官方定位是 1 对 1 实时智能体会话（或一条麦的字幕）', '按场景拆到对话 / 听写 / TTS / Chirp'],
]

FIT_GUIDE = [
    ['你的业务更像…', '优先试', '不要先试', '听哪条样例'],
    ['语音助手、接待、能打断', '对话页', '拿 Transcribe 假装会聊天', '对话 · 普通话打招呼'],
    ['让它看着摄像头说话', '对话页勾选摄像头', '指望它回传视频画面', '对话 · 摄像头'],
    ['打字问眼前的东西', '打字页勾选摄像头（会话开着约 1fps）', '当成双向视频通话或只抓一张静图', '打字 · 看见图'],
    ['直播字幕、只打字不插话', '听写页', '用对话模型再把音频当 ASR', '听写 · 普通话'],
    ['会议室里要 GA、说话人分离、批量', 'Chirp 3（另一个 Demo）', '把 Live 当 Chirp 替换', '不要在本页找 diarization'],
    ['先证明「能连上」又懒得开麦', '打字页', '一上来对着空房间说话', '打字 · 请用普通话自我介绍'],
    ['要模型说普通话', '系统指令钉 普通话', '在对话页 SpeechConfig 里填 cmn-Hans-CN', '对话页默认样例'],
]

FEATURE_VALUE = [
    ['功能 / 特性', '开了会怎样', '业务价值', '不要用来', '哪一页'],
    ['原生音频对话', '16 kHz 进、24 kHz 出，会话保持开着', '低延迟口语来回、允许打断', '当纯 ASR 或当纯 TTS', '对话'],
    ['显示你说的话', '右侧出现「你说」字幕，先草稿再定稿。关掉后模型照样听', '助手对账、无障碍、对话存档', '当 Chirp 合同级听写卖', '对话'],
    ['显示它说的话', '右侧出现「它说」字幕，和声音同步。关掉后仍出声', '字幕、合规留痕、核对语言', '当官方 STT 结果', '对话'],
    ['允许打断（VAD）', '它说话时你开口，服务端停生成、本地立刻停播', '接待、说一半被纠正——真人对话感', '外放场景（容易把自己当打断）；连上后再改开关', '对话'],
    ['打开摄像头', '约 1 帧/秒 JPEG 发给模型，它能看着画面说话。不回传视频', '导览、开箱、远程协助：看着我再回答', '双向视频通话、监控录像', '对话 / 打字'],
    ['共享屏幕', '同样约 1fps JPEG。和摄像头同时开时合成画中画再发出去', '讲 PPT、一起看报错、带看后台', '会议投屏；桌面有密钥时不要开', '对话 / 打字'],
    ['会话恢复', 'goAway 后点「接着上次」；句柄约 24 小时有效', '网络闪断或演示超过 10 分钟不断戏', '无限长会；句柄过期会丢状态', '三页都有'],
    ['上下文压缩', '滑动窗口丢掉旧轮次，音视频可超过约 2 分钟', '一直看着屏幕聊，不被两分钟踢下线', '当完整会议记录；短教学通常不必开', '三页都有'],
    ['演示函数', '可调用现在几点 / 实验室状态，气泡里看得到 tool_call', '查库存、查订单这类要接你们自己的函数', '当生产 API；不能和 Google 搜索同时开', '对话 / 打字'],
    ['Google 搜索接地', '服务端检索后再说话', '问新闻、天气等事实，少胡编', '和自定义函数写在同一次 setup；本页不出完整引用卡片', '对话 / 打字'],
    ['Affective Dialog', 'Preview。听语气，回答更急、更软或更短', '陪伴、客服安抚：口吻跟着变', '情绪识别或医疗产品；官方可能出意外效果', '对话'],
    ['Proactive Audio', 'Preview。闲聊/背景声可不接话；明确提问才开口', '厨房、车载、开放麦克风，少突然插嘴', '它必须句句接话的接待；第一次用容易以为卡死', '对话'],
    ['系统指令', '整段会话人设和语言都靠它；连上之后改了也不生效', '钉品牌语气、短句、必须用普通话回答', '补 SpeechConfig 语言表里没有的能力', '对话 / 打字'],
    ['预置声音', '换 30 个 HD 声音的音色', '选一个更适合品牌的开口声', '克隆某位真人', '对话 / 打字'],
    ['Transcribe Live', '近实时字幕，85+ 语言可自动检测', '只要字不要它插话', '电话医学、一小时文件、说话人分离', '听写'],
    ['自定义词表', '听写时专有名词更不容易写错', '品牌名、项目 ID、药品商品名', '塞日常口语；官方建议大约 100 个词', '听写'],
    ['打字回合', '同一条 Live 长连接，你打字它开口', '无麦联调、多轮打字', '当成离线 TTS；不要指望语音打断', '打字'],
]

FEATURE_BLURBS = {
    'system': {
        'effect': '整段会话的人设和语言都靠它。对话/打字页没有普通话 locale，必须在这里写「必须用普通话回答」。',
        'value': '钉品牌语气、短句、禁用某些话题。一次 setup 定下来，连上之后改了也不生效。',
        'caution': '它补不了 SpeechConfig 语言表里没有的能力，也替代不了工具和接地。',
    },
    'vocabulary': {
        'effect': '听写时专有名词更不容易写错。只对这一页的字幕生效，不会让模型开口回答。',
        'value': '品牌名、项目 ID、药品商品名少写错。',
        'caution': '官方建议大约 100 个词。不要塞日常口语，效果会变差。',
    },
    'input_transcript': {
        'effect': '右侧会出现「你说」的字幕，说话过程中会先出草稿再定稿。关掉后模型照样听，只是界面不显示你的字。',
        'value': '助手界面要对账、给听障用户看自己说了什么、把对话存档。',
        'caution': '这是对话模型附带的转写，不是 Chirp 合同级 ASR，不能当听写产品卖。',
    },
    'output_transcript': {
        'effect': '右侧会出现「它说」的字幕，和声音同步往外冒。关掉后仍会出声，只是没有它的字。',
        'value': '语音助手需要字幕、合规留痕、核对它有没有用对语言。',
        'caution': '字幕可能和实际读音不完全一致，不要当官方听写结果。',
    },
    'barge_in': {
        'effect': '它说话时你再开口，服务端 VAD 会发 interrupted，本地立刻停播并听你的新一句。关掉则它说完之前，Demo 不把麦克风送回云端。',
        'value': '接待、语音助手「说一半被纠正」——这是真人对话感的来源。',
        'caution': '外放容易把自己的声音当成打断，戴耳机更稳。必须在点开始之前勾选。',
    },
    'camera': {
        'effect': '按大约 1 帧/秒把 JPEG 发给模型，它能根据画面说话。模型不回传视频。',
        'value': '看着我、看着桌上的东西再回答：导览、开箱、远程协助的入门形态。',
        'caution': '不是双向视频通话。无压缩时音视频大约 2 分钟。不要当监控录像。',
    },
    'screen': {
        'effect': '共享屏幕同样按大约 1 帧/秒发 JPEG。和摄像头同时开时，合成一张画中画（屏幕是大图，摄像头在右下角小窗）再发出去。',
        'value': '讲解 PPT、一起看报错页面、带看后台。',
        'caution': '不是会议投屏。官方没有双路视频。桌面上有密钥或客户数据时不要开。',
    },
    'session_resume': {
        'effect': '服务会下发恢复句柄。大约 10 分钟 WebSocket 限额触发 goAway 后，可点「接着上次」把上下文接到下一根线。句柄大约 24 小时内有效。',
        'value': '网络闪断、演示超过 10 分钟时不断戏，用户不用从头自我介绍。',
        'caution': '不是无限长会。句柄过期或当时不可恢复，状态会丢。必须在点开始之前勾选。',
    },
    'compress': {
        'effect': '上下文接近上限时，服务端用滑动窗口丢掉或压缩旧轮次，会话可以超过无压缩时的大约 2 分钟（音视频）或 15 分钟（纯音频）。',
        'value': '需要「一直看着屏幕聊」，而不是两分钟被踢下线。',
        'caution': '较早的对话可能被忘掉，不能当完整会议记录。短教学通常不必开。',
    },
    'affective': {
        'effect': 'Preview。模型会尝试听你的语气和情绪，并调整回答风格（更急、更软、更短）。',
        'value': '陪伴、客服安抚：听得出用户着急或低落时，口吻跟着变。',
        'caution': '官方写明可能出现意外效果。不要当情绪识别或医疗产品。必须在点开始之前勾选。',
    },
    'proactive': {
        'effect': 'Preview。闲聊、自言自语、背景电视可以不接话；被明确提问时才开口。它沉默时不收输出音频费，但输入音频仍计费。',
        'value': '厨房、车载、开放麦克风：减少「没叫它却突然插嘴」。',
        'caution': '第一次用很容易以为卡死。必须在点开始之前勾选。不要和「它必须句句接话」的接待场景一起开。',
    },
    'tools': {
        'effect': '「不接」就是纯开口聊天。「演示函数」让它能调用现在几点 / 实验室状态，气泡里看得到工具调用。「Google 搜索」由服务端检索后再说话。',
        'value': '查库存、查订单要接你们自己的函数；问新闻、天气等事实用搜索接地，少胡编。',
        'caution': '官方不允许搜索工具和自定义函数写在同一次 setup。本页演示函数是假数据。必须在点开始之前选好。',
    },
}

API_OUT_OF_DEMO = [
    ['能力', '业务价值', '为什么网页 Demo 不做', '客户接入文档'],
    [
        'Grounding with Vertex RAG Engine',
        '让助手按你们知识库回答（制度、SKU、工单流程），而不是只靠搜索或临场发挥',
        '要先有 RAG corpus 资源名。本页 Google 搜索不需要 corpus；官方不允许搜索和自定义函数写在同一次 setup。',
        '配置 Gemini 能力（含 RAG）\nhttps://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api/configure-gemini-capabilities',
    ],
]

WORKSPACES = [
    {
        'id': 'talk', 'nav': '对话',
        'eyebrow': 'GEMINI LIVE · NATIVE AUDIO', 'title': '对着麦克风说话，它接话。',
        'lead': '这一页是语音助手：16 kHz 进去，24 kHz 出来。默认允许打断（服务端 VAD）。可选打开摄像头：官方把视频当成 JPEG，最多 1 帧/秒；无压缩时音视频大约 2 分钟。模型只看不回传画面。普通话写进系统指令——SpeechConfig 表没有 cmn-Hans-CN。区域 us-central1，不是 global。',
        'positioning': {
            'official': '官方定位：Gemini Live 原生音频会话（AUDIO）。1 对 1 实时语音助手，不是会议系统、不是 Chirp、不是 TTS。',
            'this_page': '本页：你对着麦克风说，它用 24 kHz PCM 接话。可打断。可选 JPEG 约 1 帧/秒。',
            'not_this': '不要用本页做：纯听写、电话/医学 ASR、一小时会、要模型回传画面、批量念稿。',
        },
        'model': MODEL_TALK,
        'features': ['live', 'mic', 'camera', 'screen', 'barge_in', 'voice', 'system', 'language', 'input_transcript', 'output_transcript', 'session_resume', 'compress', 'affective', 'proactive', 'tools'],
        'advantages': [
            'GA 原生音频模型，适合接待、语音助手、边走边问、插话打断。',
            '转写开关只是字幕，不是把这一页变成 Chirp。',
            '中文请写进系统指令。官方原文提示：RESPOND IN LANGUAGE. YOU MUST RESPOND UNMISTAKABLY IN LANGUAGE.',
        ],
        'limit_note': 'WebSocket 大约 10 分钟，结束前约 60 秒 goAway。无压缩：纯音频约 15 分钟，带摄像头约 2 分钟。打断靠服务端 VAD；外放时请大声插话或戴耳机。摄像头是 JPEG 1fps，不是双向视频通话。不要在 SpeechConfig 里填普通话 locale。Vertex Live 同一会话只能选一种输出模态：这一页是 AUDIO。',
        'fit': [
            {'title': '适合', 'body': '要模型开口回答、插话打断、可选让它看见摄像头、会话留在这一通连接里。'},
            {'title': '不适合', 'body': '纯听写、电话 8 kHz、医学口授、一小时会议出稿、要模型回传视频画面。'},
        ],
        'coverage': '声音下拉是 Live 官方 30 个 voice_name。语言下拉是 SpeechConfig 官方表（无普通话）外加「不指定」。',
        'surface': [
            'LiveConnectConfig response_modalities AUDIO',
            'SpeechConfig.voice_name',
            'system_instruction',
            'input_audio_transcription / output_audio_transcription',
            'send_realtime_input audio/pcm;rate=16000',
            'send_realtime_input video image/jpeg 1fps（摄像头或屏幕）',
            'barge-in / interrupted / START_OF_ACTIVITY_INTERRUPTS',
            'session_resumption handle',
            'context_window_compression sliding_window',
            'tools：演示函数或 google_search（不可同时）',
            'enable_affective_dialog / proactivity.proactive_audio',
        ],
        'docs': [DOC_LIVE, DOC_SESSION, DOC_VOICE],
        'languages': NATIVE_LANGUAGES,
        'language_hint': '这里的语言码是模型开口用的 SpeechConfig.language_code，不是 Chirp 的 language_codes。表里没有普通话。要说中文：语言选「不指定」，把「必须用普通话回答」写进系统指令。',
    },
    {
        'id': 'transcribe', 'nav': '听写',
        'eyebrow': 'GEMINI 3.5 TRANSCRIBE · LIVE PREVIEW', 'title': '只要字幕，不要它插话。',
        'lead': '这一页是生成式听写：response_modalities=["TEXT"]，模型 ID 是 gemini-3.5-transcribe-live-preview。官方区域 global，最长约 10 分钟。它不会回答「今天天气怎么样」——那是对话页的事。这也不是 Chirp 3 的 StreamingRecognize。',
        'positioning': {
            'official': '官方定位：Gemini 3.5 Transcribe Live（Preview）。生成式实时听写，只出字幕，不会接话。',
            'this_page': '本页：对着麦克风听写。response_modalities 只有 TEXT。区域 global。单声道 16 kHz。',
            'not_this': '不要用本页做：语音助手、说话人分离、多声道、Chirp 合同听写、让它回答问题。',
        },
        'model': MODEL_TRANSCRIBE,
        'features': ['live', 'mic', 'vocabulary', 'language', 'session_resume', 'compress'],
        'advantages': [
            '官方写明：Agent Platform 上的听写主力之一；Live 路径支持自动语言检测（85+）和自定义词表。',
            '普通话 cmn-Hans-CN 在这一页的语言表是 Supported。对话页的 SpeechConfig 表没有它，不要混。',
            '说话人分离、词级时间戳在文件接口（gemini-3.5-transcribe-preview）上，Live 这条没有 diarization。',
        ],
        'limit_note': 'Preview。本页只用麦克风实时听写，单声道 16 kHz。没有说话人分离、没有多声道/分轨。那些在文件模型 gemini-3.5-transcribe-preview 或 Chirp 3 上。发送音频前必须等 setup_complete（SDK connect 返回后即可）。',
        'fit': [
            {'title': '适合', 'body': '近实时字幕、现场记录、想试 3.5 Transcribe 而不是 Chirp。只用麦克风。'},
            {'title': '不适合', 'body': '语音助手、电话医学、GA 合同级 ASR、一小时文件。'},
        ],
        'coverage': '语言下拉是 3.5 Transcribe 官方表里的 Supported 项，加上 auto 和少量 Experimental。完整 85+ 见官方语言表。',
        'surface': [
            'model=gemini-3.5-transcribe-live-preview',
            'response_modalities TEXT',
            'input_audio_transcription.language_codes',
            'custom_vocabulary',
            'interim_input_transcription / input_transcription',
            'location=global',
            'session_resumption / context_window_compression',
        ],
        'docs': [DOC_TRANSCRIBE, DOC_LIVE, DOC_SESSION],
        'languages': TRANSCRIBE_LANGUAGES,
        'language_hint': '已知语言时填 locale 更准。选 auto 则不发送 language_codes，让模型自己检测。自定义词表只放品牌、项目 ID，不要塞日常口语。',
    },
    {
        'id': 'textturn', 'nav': '打字',
        'eyebrow': 'GEMINI LIVE · TEXT IN · AUDIO OUT', 'title': '先打字，让它开口。',
        'lead': '同一套原生音频模型、同一条 Live 长连接：你打字，它用 24 kHz PCM 说话。跟对话页的差别主要是输入方式（send_client_content 文本 vs send_realtime_input 麦克风）。适合第一次证明「项目、ADC、区域、声音」是通的。这仍是 Live 会话，不是 Cloud TTS。',
        'positioning': {
            'official': '官方定位：同一条 Live 原生音频会话。官方支持文本输入（send_client_content）+ 音频输出。',
            'this_page': '本页：打字进去、它说话出来。连接一直开着，改字后再发即可。点停止才挂断。摄像头与对话页相同：约 1 帧/秒 JPEG。',
            'not_this': '不要用本页做：Cloud TTS / SSML 配音流水线、语音打断（没有麦克风就没有 VAD）、指望它当万能接口。',
        },
        'model': MODEL_TALK,
        'features': ['text', 'voice', 'system', 'language', 'camera', 'screen', 'session_resume', 'compress', 'tools'],
        'advantages': [
            '无麦也能走通 Vertex Live：看得到请求预览，听得到声音，可以多轮打字不挂断。',
            '可勾选摄像头：会话开着就按约 1 帧/秒推 JPEG，和对话页同一套约定。',
        ],
        'limit_note': '点「请模型说」打开长连接；之后按钮变成「再发一句」。点停止才挂断。打断（VAD）这一页用不上，因为没有麦克风。摄像头是 JPEG 1fps，不是双向视频。长文本、SSML、多角色请用 TTS 产品。',
        'fit': [
            {'title': '适合', 'body': '联调、演示、听音色、改人设、多轮打字、打字问眼前画面。'},
            {'title': '不适合', 'body': '实时语音打断、直播字幕、批量合成。'},
        ],
        'coverage': '声音与语言下拉和对话页相同。普通话同样靠系统指令，不要填 cmn-Hans-CN。',
        'surface': [
            'LiveConnectConfig AUDIO',
            'send_client_content 文本回合（长连接可多轮）',
            '可选 send_realtime_input video JPEG（摄像头或屏幕）',
            'session_resumption / context_window_compression',
            'tools：演示函数或 google_search',
            'output audio 24 kHz PCM',
            '可选输出转写',
        ],
        'docs': [DOC_LIVE, DOC_SESSION, DOC_VOICE],
        'languages': NATIVE_LANGUAGES,
        'language_hint': '和对话页同一张 SpeechConfig 语言表。中文：语言留空，系统指令写必须用普通话。',
    },
]

DOCS = [DOC_LIVE, DOC_SESSION, DOC_VOICE, DOC_CAP, DOC_TRANSCRIBE, DOC_ADC, DOC_CHIRP]
