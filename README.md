# 对话实验室 · Gemini Live API

本地教学 Demo：用浏览器试 **Vertex / Agent Platform 上的 Gemini Live API**。Python FastAPI，没有 Node 前端。

这不是 Google 官方产品。资料核查日期：**2026-09-10**。

它也不是 Cloud Speech-to-Text。Chirp 3 的 `StreamingRecognize` 是另一条产品、另一套价目、另一个区域模型。

## 你能在页面上试什么

| 顶栏 | 模型 | 区域 | 做什么 |
| --- | --- | --- | --- |
| 对话 | `gemini-live-2.5-flash-native-audio`（GA） | `us-central1` | 麦克风进去，模型用 24 kHz PCM 说话；可打断；可选摄像头 JPEG 1fps |
| 听写 | `gemini-3.5-transcribe-live-preview`（Preview） | `global` | 只要字幕，不会接话 |
| 打字 | 同上原生音频模型 | `us-central1` | 打字进去，模型说话；同一条长连接，可再发一句；可选 JPEG 1fps |

预览请求**不会**调用 Google。点「开始对话 / 开始听写 / 请模型说」才会打开 Live WebSocket，并可能产生费用。打字页连上之后改字再点「再发一句」；点停止才挂断。

Live **不是万能接口**。官方定位是 **1 对 1 实时会话**（语音助手或一条麦的生成式字幕），不是 Chirp、不是 Cloud TTS、不是会议纪要、不是双向视频通话。顶栏三页对应该三条官方入口，不要混用。

## 1. 准备 Cloud 项目

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
gcloud services enable aiplatform.googleapis.com --project YOUR_PROJECT_ID
```

复制环境变量：

```bash
cp .env.example .env
# 填写 GOOGLE_CLOUD_PROJECT
# GOOGLE_CLOUD_LOCATION=us-central1
```

不要把 `global` 当成对话页的区域。那是 TTS 和 Transcribe Live 常用的值；原生音频 Live 是区域接口。听写页会**自动改成 global**。

## 2. 安装并启动

需要 Python 3.11+。

```bash
cd LiveDemo
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8003
```

浏览器打开 http://127.0.0.1:8003

本机若已有 TTS Demo（8001）或 ASR Demo（8002），不要抢端口。Live 默认 **8003**。

## 3. 建议的点击顺序

1. **打字**页 → 样例「请用普通话自我介绍」→ 预览 → 请模型说 → 改一句再发 → 停止才挂断  
2. **听写**页 → 点开始听写 → 对着麦克风说话  
3. **对话**页 → 样例「普通话打招呼」→ 打开麦克风说「你好」  
4. 同一页 → 样例「打断」：等它开口再插话；样例「摄像头」：勾选摄像头问它看见了什么  
5. **打字**页也可勾选摄像头（样例「看见图」）：会话开着约 1 帧/秒 JPEG，没有语音打断

打断和视频都是官方 Live 能力：打断靠服务端 VAD（`interrupted`）；视频是 JPEG，最多 1 帧/秒。模型**不回传画面**。无压缩时音视频会话大约 **2 分钟**。

普通话注意：

- 听写页语言表有 `cmn-Hans-CN`
- 对话 / 打字页的 SpeechConfig 官方语言表**没有**普通话。语言选「不指定」，把「必须用普通话回答」写进系统指令

## 4. 输入输出格式

| 方向 | 格式 |
| --- | --- |
| 浏览器 → Live | 16 kHz PCM；可选 JPEG 视频帧（最多 1 帧/秒） |
| Live → 浏览器 | 24 kHz PCM（没有视频输出） |
| 连接 | 有状态 WSS `BidiGenerateContent` |
| 时长 | 按页看，总表只在入门指南。三页换线都大约 10 分钟（心跳挡不住；`goAway` 提前约 60 秒 → 会话恢复）。对话页只开口、不压缩时上下文大约 15 分钟，往往先撞换线；开画面不压缩大约 2 分钟。打字页没有单独分钟数，换线仍是 10 分钟，不要套 15 分钟。听写大约 10 分钟 |

## 5. 命令行最小示例

```bash
.venv/bin/python examples/quickstart.py
```

这会发起一次真实的 Live 调用（打字 → 音频），可能计费。

## 6. 离线测试

```bash
.venv/bin/python -m pytest -q
```

测试不访问 Google。听写页只走麦克风，不再附带预录 WAV。

## 7. 常见失败

| 现象 | 先查 |
| --- | --- |
| 预览可以、开始失败 | ADC、项目 ID、`aiplatform.googleapis.com`、账单 |
| 提示 SOCKS / python-socks，或对话/听写「结束了」但没字 | 本机 Clash 把系统代理设成了 SOCKS。重启 Demo：启动时会改走同一端口的 HTTP 代理。Clash 需允许终端 |
| 404 模型不存在 | 对话页是否误用了 `global`；听写页是否误用了 `us-central1` |
| 400 模态错误 | 听写页必须 `TEXT`，不要要模型说话 |
| 对话页填 `cmn-Hans-CN` 被拒 | 请改系统指令钉普通话 |
| 空字幕 | 是否在 `setup_complete` / SDK `connect` 返回之前就推音频 |
| 连接约 10 分钟断 | 三页都会。单根 Live 连接的服务端上限，不是心跳失败。打字页也一样。勾选会话恢复后马上点「接着上次」 |
| 开着摄像头大约 2 分钟断 | 128k 上下文被 JPEG 装满，不是 10 分钟换线。勾选上下文压缩，或关掉画面 |

## 本 Demo 明确不做

模型回传画面、RAG Engine 接地、文件转写模型 `gemini-3.5-transcribe-preview`、ADK / LiveKit、Chirp / 电话 / 医学。屏幕共享、会话恢复、上下文压缩、演示函数、Google 搜索接地、Affective Dialog / Proactive Audio 已在页面开关里。详见「入门指南」。

## 架构

浏览器只连你的本机后端。ADC 留在服务器，不会进前端。

```
浏览器  --WS/HTTP-->  FastAPI (127.0.0.1:8003)  --WSS-->  Vertex Live API
```
