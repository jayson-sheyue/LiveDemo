"""最小可运行的 Vertex Live 示例：发一句文本，收下 24 kHz PCM。

用法（在项目根目录）：
    .venv/bin/python examples/quickstart.py

需要：
    gcloud auth application-default login
    gcloud auth application-default set-quota-project YOUR_PROJECT_ID
    .env 里的 GOOGLE_CLOUD_PROJECT
    已启用 aiplatform.googleapis.com

这会发起一次真实的付费/配额调用。
对照：https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api/start-manage-session
"""
from __future__ import annotations

import asyncio
import os
import wave
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')

OUT = ROOT / 'outputs' / 'quickstart.wav'
MODEL = 'gemini-live-2.5-flash-native-audio'
LOCATION = 'us-central1'
TEXT = '请用一句很短的普通话介绍你自己。'


def save_wav(path: Path, pcm: bytes, rate: int = 24000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(pcm)


async def main() -> None:
    project = (os.getenv('GOOGLE_CLOUD_PROJECT') or '').strip()
    if not project:
        raise SystemExit('请在 .env 填写 GOOGLE_CLOUD_PROJECT')
    client = genai.Client(vertexai=True, project=project, location=LOCATION)
    config = types.LiveConnectConfig(
        response_modalities=['AUDIO'],
        system_instruction=types.Content(
            parts=[types.Part(text='RESPOND IN MANDARIN. YOU MUST RESPOND UNMISTAKABLY IN 普通话。用一句短话。')]
        ),
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name='Kore')
            )
        ),
    )
    pcm = bytearray()
    async with client.aio.live.connect(model=MODEL, config=config) as session:
        await session.send_client_content(
            turns=[types.Content(role='user', parts=[types.Part(text=TEXT)])],
            turn_complete=True,
        )
        async for message in session.receive():
            data = getattr(message, 'data', None)
            if data:
                pcm.extend(data)
            sc = getattr(message, 'server_content', None)
            if sc and getattr(sc, 'turn_complete', False):
                break
    if not pcm:
        raise SystemExit('没有收到音频。请检查区域 us-central1 与模型 ID。')
    save_wav(OUT, bytes(pcm))
    print(f'wrote {OUT} ({len(pcm)} bytes PCM)')


if __name__ == '__main__':
    asyncio.run(main())
