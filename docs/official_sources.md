# Gemini Live API 官方参考资料索引

核查日期：2026-09-10。检索范围：Google Cloud Documentation · Gemini Enterprise Agent Platform · Gemini 3.5 Transcribe。

本项目不是 Google 官方产品。“全部”指覆盖本 Demo 用到的主干文档，不宣称穷尽历史版本、论坛帖或未来页面。

官方把 Live API 定位成 **1 对 1 低延迟双向会话**（原生音频助手，或 Transcribe Live 字幕），不是 Chirp、不是 TTS、不是会议系统。顶栏三页对应三种入口，不要指望一个按钮万能。

## 先读这几个

| 官方链接 | 能解决的问题 | 对应项目位置 |
| --- | --- | --- |
| [Gemini Live API 概览](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api) | 原生音频会话、和普通 generateContent 的差别 | 对话页；catalog.py |
| [开始并管理会话](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api/start-manage-session) | 换线约 10 分钟（心跳无效 → 会话恢复）；无压缩纯语音约 15 分钟 / 开画面约 2 分钟（128k → 压缩）；打字页换线仍是 10 分钟、没有单独分钟数；goAway、16/24 kHz | 入门页「能撑多久」总表；各功能页只写本页影响；live.py |
| [语言与声音](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api/configure-language-voice) | 30 个 `voice_name`；SpeechConfig 语言表（无普通话）；VAD | 对话 / 打字页 |
| [Live API 参考（打断 / 视频帧率）](https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/models/multimodal-live) | barge-in 默认 `START_OF_ACTIVITY_INTERRUPTS`；视频按 1 FPS 处理 | 对话页打断与摄像头 |
| [Gemini 3.5 Transcribe](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-5-transcribe) | `gemini-3.5-transcribe-live-preview`、global、最多约 10 分钟、language_codes、自定义词表；Live 无 diarization | 听写页 |
| [ADC 配置](https://docs.cloud.google.com/docs/authentication/provide-credentials-adc) | 本地登录 | README 第 1 节 |

## 能力与边界

| 官方链接 | 用途 |
| --- | --- |
| [配置 Gemini 能力](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api/configure-gemini-capabilities) | 工具、Affective Dialog、Proactive Audio 已在对话页。RAG Engine 要 corpus，见入门页「网页故意没接」 |
| [Python Gen AI SDK](https://googleapis.github.io/python-genai/) | `client.aio.live.connect` |
| [启用 Vertex AI API](https://console.cloud.google.com/flows/enableapi?apiid=aiplatform.googleapis.com) | 403 / API 未启用 |

## 相关但不是本 Demo 的路径

这些页面容易和 Live 搜到一起。

| 官方链接 | 用途 |
| --- | --- |
| [Gemini API Live（AI Studio / API Key）](https://ai.google.dev/gemini-api/docs/live-api) | 不是 Vertex 这条；本 Demo 不接 API Key |
| [Chirp 3 Transcription](https://docs.cloud.google.com/speech-to-text/docs/models/chirp-3) | GA 听写、StreamingRecognize。字幕场景有重叠，协议和合同都不同 |
| [流式识别](https://cloud.google.com/speech-to-text/docs/streaming-recognize) | Speech-to-Text 的实时听写 |
| [Gemini-TTS](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts) | 把稿子念出来，不是 Live 会话 |
| [Speech-to-Text 定价](https://cloud.google.com/speech-to-text/pricing) | Chirp 价目，不是 Live 价目 |
