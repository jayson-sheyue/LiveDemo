from __future__ import annotations

from pathlib import Path

REQUIRED_URLS = [
    'https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api',
    'https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api/start-manage-session',
    'https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api/configure-language-voice',
    'https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/models/multimodal-live',
    'https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-5-transcribe',
    'https://docs.cloud.google.com/docs/authentication/provide-credentials-adc',
    'https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api/configure-gemini-capabilities',
    'https://ai.google.dev/gemini-api/docs/live-api',
    'https://docs.cloud.google.com/speech-to-text/docs/models/chirp-3',
    'https://cloud.google.com/speech-to-text/docs/streaming-recognize',
]


def test_required_docs_exist():
    root = Path(__file__).resolve().parents[1]
    for name in ('README.md', 'learning_guide.md', 'docs/official_sources.md'):
        assert (root / name).is_file()
        assert len((root / name).read_text(encoding='utf-8')) > 500


def test_official_index_covers_主干入口():
    text = (Path(__file__).resolve().parents[1] / 'docs/official_sources.md').read_text(encoding='utf-8')
    missing = [url for url in REQUIRED_URLS if url not in text]
    assert missing == []


def test_learning_guide_covers_can_and_cannot():
    text = (Path(__file__).resolve().parents[1] / 'learning_guide.md').read_text(encoding='utf-8')
    for needle in (
        '能干什么', '不能干什么', '对话页', '听写', '打字',
        'cmn-Hans-CN', '普通话', 'us-central1', 'global',
        'StreamingRecognize', 'goAway', '16 kHz', '24 kHz',
        'Chirp', 'setup', '系统指令',
        '打断', 'JPEG', '2 分钟',
        '不是万能', '1 对 1', 'send_client_content', '再发一句',
        '会话恢复', '上下文压缩', 'Google 搜索',
        '开了会怎样', '业务价值', '不要用来',
        '网页故意没接', 'RAG',
    ):
        assert needle in text, needle
    readme = (Path(__file__).resolve().parents[1] / 'README.md').read_text(encoding='utf-8')
    assert 'GOOGLE_CLOUD_LOCATION=us-central1' in readme
    assert 'aiplatform.googleapis.com' in readme
    assert '8003' in readme
    assert (Path(__file__).resolve().parents[1] / 'examples' / 'quickstart.py').is_file()
