# 对话实验室 · 入门指南

这份指南假设你第一次听到「Live API」。不需要先懂 WebSocket、Vertex 或 Chirp。

**读完并点几下 Demo 之后，你应该能回答：**

1. Live 是干什么的，为什么它**不是万能**（不是 Chirp、不是 TTS、不是会议系统）
2. 顶栏三页分别给谁用：对话 / 听写 / 打字的官方差别是什么
3. 为什么打字页和对话页走同一条长连接，差别主要是你打字还是开口
4. 为什么对话页不能在语言框里填普通话
5. 为什么听写页的区域是 global，对话页却是 us-central1
6. 出问题该打开哪份官方文档

请先按 [README.md](README.md) 把页面打开。没有登录也可以读文档、点样例、用「预览请求」；**只有真正开始会话才会把音频或文本发到 Google，并可能产生费用。**

资料核查日期：2026-09-10。本项目不是 Google 官方产品。

---

## 0. 它到底是什么（先建立图像）

### 一句话

**Gemini Live API = 一条开着的电话线。** 线还在，双方都可以继续说；WebSocket 大约 10 分钟会 `goAway`。勾选会话恢复后，可以点「接着上次」把上下文接到下一根线（句柄大约 24 小时有效）。不恢复的话，线一挂，这段对话的现场状态就结束了。

### 能干什么 / 不能干什么

**能干什么：** 语音助手（开口回答、插话打断、可选让它看见摄像头）、近实时字幕、用系统指令钉语言和人设、换 30 个预置声音、先打字再听它说。

**不能干什么：** 当 Chirp 用（电话、医学、批量、合同级 GA 听写）、当 Cloud TTS 流水线用、离线部署、克隆声纹、一次开一小时会、双向视频通话、会议室说话人分离。WebSocket 大约 10 分钟会 `goAway`。发送音频前要等会话 `setup` 完成（SDK `connect` 返回即表示 setup 已完成）。

### Live 不是万能

官方把 Live 定位成 **1 对 1 的低延迟双向会话**（语音智能体，或一条麦克风的生成式字幕），**不是**「凡是语音相关都走这一个按钮」。

不要拿 Live 提这些需求：

- 一小时会议出稿、说话人分离、多声道分轨 → Chirp / 文件转写
- 把稿子念出来、SSML、多角色配音 → Cloud TTS / Gemini-TTS
- 电话 8 kHz、医学口授、合同级 GA ASR → Speech-to-Text
- 要对端也出画面 → Live 只收 JPEG 帧，模型不回传视频

顶栏三页也不是三个万能工作台，只是 Live 里三种**官方入口**：AUDIO 对话、TEXT 听写、文本输入 + 音频输出。

它**不是**：

- Cloud Speech-to-Text / Chirp（那是专职速记员，不会回答问题）
- Cloud TTS / Gemini-TTS（那是把稿子念出来，通常一次请求一段音频）
- 普通的 `generateContent` 聊天（那是一问一答的 HTTP，不是双向音频流）

### 工作台在干什么

| 你在页面上点的 | 生活里像什么 | 业务上换来什么 |
| --- | --- | --- |
| 对话 · 打开麦克风 | 打电话给助手 | 语音接待、边走边问、允许打断 |
| 对话 · 打开摄像头 | 让它看见你再开口 | 不是双向视频通话；JPEG 1 帧/秒 |
| 听写 · 对着麦克风听写 | 开会字幕机，只打字不插话 | 近实时字幕（生成式听写，Preview） |
| 打字 · 请模型说 / 再发一句 | 同一条电话线，你打字它说话 | 无麦联调；多轮打字不挂断 |
| 系统指令 | 会前交代「用普通话、短句」 | 钉语言、人设、长短 |
| 预置声音 | 换一个说话的人 | 30 个 HD 音色，不是克隆真人 |
| 预览请求 | 先看这封信怎么写，不寄出 | 不产生 Live 费用 |

---

## 1. 三个必须先懂的差别

### 1.1 对话页：它会接话

模型：`gemini-live-2.5-flash-native-audio`（GA）。

麦克风 16 kHz PCM 进去，模型 24 kHz PCM 出来。连接不会因为一轮结束而挂断。

**打断（barge-in）：** 官方可以开关。默认 `START_OF_ACTIVITY_INTERRUPTS`，关掉则是 `NO_INTERRUPTION`。Demo 对话页有勾选框，**开始会话前**生效；连上之后改开关请先停止再开始（setup 一般不能中途改）。

**视频：** 官方输入是 JPEG，最多 **1 帧/秒**。无压缩时音视频会话大约 **2 分钟**（纯音频大约 15 分钟）。模型**不回传画面**，只会看着说。这不是 FaceTime 那种双向视频通话。对话页也可以共享屏幕。摄像头和屏幕同时开时，Demo 合成一张画中画（仍是一条 1fps JPEG），因为官方没有双路视频。

可选的输入/输出转写只是字幕，**不会**把这一页变成 Chirp。

对话页 **第 02 步**每个开关下面都写了「开了会怎样 / 业务价值 / 不要用来」。入门指南里「每个开关的业务价值」表是同一份说明。

**这一页还能开的官方开关（开始前勾选）：**

- **显示你说的话 / 显示它说的话**：右侧出字幕。关掉后照样听、照样说，只是界面不显示字。用来对账和存档，不是 Chirp 合同级 ASR。
- **允许打断**：它说话时你开口，服务端 VAD 发 `interrupted`，本地立刻停播。接待和「说一半被纠正」靠这个。外放容易把自己的声音当打断，戴耳机更稳。
- **摄像头 / 共享屏幕**：各约 1 帧/秒 JPEG。两路同时开时 Demo 合成画中画再发出去。模型只看不回传画面。不是会议投屏，也不是双向视频。
- **会话恢复**：服务下发 handle；大约 10 分钟 `goAway` 后点「接着上次」。句柄大约 24 小时内有效。不是无限长会。
- **上下文压缩**：滑动窗口。音视频想超过约 2 分钟时再开；旧轮次可能被裁掉，不能当完整会议记录。
- **演示函数 / Google 搜索**：官方不允许两者写在同一次 setup。演示函数是本地假数据 `get_current_time` / `get_lab_status`。搜索用来少胡编事实。
- **Affective Dialog**：Preview。按语气调整回答（更急、更软、更短）。陪伴/客服安抚；不要当情绪识别或医疗产品。官方提示可能出意外效果。
- **Proactive Audio**：Preview。闲聊或背景声可以不接话；明确提问才开口。厨房/车载少突然插嘴。它沉默时不收输出音频费，但输入音频仍计费。第一次用容易以为卡死。

### 1.2 听写页：它只打字

模型：`gemini-3.5-transcribe-live-preview`（Preview）。

官方区域 **global**。`response_modalities=["TEXT"]`。本页只用麦克风，不推预录音频。你问「今天天气怎么样」，它最多把这句听写成字，不会预报天气。

这不是 `StreamingRecognize`，也不是 Chirp 3。说话人分离、多声道/分轨、词级时间戳：Live 听写都没有。文件接口 `gemini-3.5-transcribe-preview` 支持说话人分离（最多约 8 人）；电话/多轨请用 Chirp 3（听写实验室）。

### 1.3 打字页：同一条线，只是你打字

还是原生音频 GA 模型，还是 Live 长连接。官方输入改成 `send_client_content`（文本），输出仍是 24 kHz 说话。跟对话页的差别**主要是用户输入方式**，不是另做一个 TTS 产品。

点「请模型说」打开会话并发送第一句；之后按钮变成「再发一句」。点停止才挂断。

可勾选摄像头：和对话页一样，会话开着就按约 **1 帧/秒**推 JPEG，不是点一下抓一张静图。这一页没有麦克风，所以没有语音打断。

这仍是 Live 会话，不是 Cloud TTS。没有 SSML、没有多角色配音流水线。

---

## 2. 普通话为什么这么别扭

官方 [语言与声音](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api/configure-language-voice) 里，**SpeechConfig.language_code** 的表格目前没有 `cmn-Hans-CN`。

所以：

- **对话 / 打字**：语言选「不指定」，系统指令写  
  `RESPOND IN MANDARIN. YOU MUST RESPOND UNMISTAKABLY IN 普通话。`
- **听写**：可以直接选 `cmn-Hans-CN`。Gemini 3.5 Transcribe 的语言表把普通话标成 Supported。

不要把 Chirp 的 locale 习惯抄到对话页的语言框里。本 Demo 会拒绝 `cmn-Hans-CN` 出现在对话/打字的 SpeechConfig 里，避免你以为「填了就会变中文」。

---

## 3. 区域不要抄错

| 工作台 | 本 Demo 实际使用的区域 | 常见抄错 |
| --- | --- | --- |
| 对话 / 打字 | `us-central1` | 抄 TTS 的 `global` → 模型 404 |
| 听写 | `global` | 抄对话页的 `us-central1` → 模型 404 |

`.env` 里的 `GOOGLE_CLOUD_LOCATION=us-central1` 是给对话页的默认值。听写页会改写为 global，并在预览里警告你。

---

## 4. 能撑多久（按页看，对业务）

总对照表只在入门指南页。对话 / 听写 / 打字各页只写本页会碰到的情况。

WebSocket 协议可以 24×7 开着，心跳也能防 NAT 踢空闲连接，但 **挡不住** Google 给这根 Live 连接设的关线时间。

**对话页：** 门店接待、语音助手大约 **10 分钟** 会突然没声（换线），客人要重新自我介绍，除非自动「接着上次」。不开摄像头时，窗口大约还能再撑到 **15 分钟**，所以纯语音先卡在换线上。一开摄像头或屏幕，不压缩大约 **2 分钟**，只够短导览，不够一路讲解。

**打字页：** 不是「打字就能聊一整天」。单根线仍然大约 **10 分钟** 会挂。你打一句它回一句，窗口涨得比麦克风一直开着慢，官方也没有单独给打字一个分钟数——不要把对话页的 15 分钟套过来。打字时若开着摄像头/屏幕，和对话页一样，不压缩大约 **2 分钟**。

**听写页：** 现场字幕大约 **10 分钟** 一切两断，不能当整场发布会的速记员。一小时会走 Speech-to-Text 批量。

要一直开着：压缩和恢复都开。只开一个，另一条仍会先断。

出处：[开始并管理会话](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api/start-manage-session)。

---

## 5. 和 Chirp 实时听写怎么选

两者都能「边说边出字」，重叠的只是**直播字幕**这一个场景。

选 **Chirp / Speech-to-Text**，如果你需要：GA 合同级 ASR、电话 8 kHz、医学 en-US、批量、1–8 轨、V2 识别器那一套。

选 **Live 听写**，如果你已经在 Agent Platform / Gemini 栈上，想试 3.5 Transcribe 的实时路径，并能接受 Preview。

选 **Live 对话**，如果你要模型**开口回答**，而不是只打稿。

---

## 6. 架构（为什么浏览器不直连 Google）

```
你的麦克风 / 可选摄像头 JPEG
        ↓
  本机 FastAPI（ADC 在这里）
        ↓
  Vertex Live：BidiGenerateContent
```

密钥和 ADC 留在服务器。前端只跟 `127.0.0.1:8003` 说话。

### 网页故意没接的 Live 能力

入门页那张表只列 **Live API 自己有、但网页当场做不了** 的能力。目前是 **Vertex RAG Engine 接地**：客户要把制度、SKU 接到助手上时，按 [配置 Gemini 能力](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api/configure-gemini-capabilities) 准备 corpus 资源名。本页 Google 搜索不需要 corpus。

下面这些 **不要** 写进那张表：模型不回传视频（Live 做不到，不是没接）；Chirp / 文件转写 / ADK / LiveKit（别的产品或应用层）。

---

## 7. 出问题看哪份文档

| 现象 | 打开 |
| --- | --- |
| 不知道 Live 是什么 | [Live API 概览](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api) |
| 10 分钟断、2 分钟断、打字也挂、goAway、心跳没用 | [开始并管理会话](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api/start-manage-session) · 入门页「能撑多久」 |
| 声音列表、语言表没有普通话 | [语言与声音](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api/configure-language-voice) |
| 听写模型 ID、global、85+ 语言 | [Gemini 3.5 Transcribe](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-5-transcribe) |
| 登录失败 | [ADC](https://docs.cloud.google.com/docs/authentication/provide-credentials-adc) |
| 其实你要的是 Chirp | [Chirp 3](https://docs.cloud.google.com/speech-to-text/docs/models/chirp-3) |

完整索引见 [docs/official_sources.md](docs/official_sources.md)。
