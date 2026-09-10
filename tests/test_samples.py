from __future__ import annotations

from samples import load_samples


def test_samples_partitioned_by_engine():
    samples = load_samples()
    assert {item['engine'] for item in samples} == {'talk', 'transcribe', 'textturn'}
    transcribe = [item for item in samples if item['engine'] == 'transcribe']
    assert all(not item.get('audio') for item in transcribe)
    talk = [item for item in samples if item['engine'] == 'talk']
    assert all(not item.get('audio') for item in talk)
    textturn = [item for item in samples if item['engine'] == 'textturn']
    assert all(item['config'].get('text') for item in textturn)
    assert any(item['config'].get('language') == 'cmn-Hans-CN' for item in transcribe)
    assert any(item['config'].get('language') == '' for item in talk)
    assert any(item['config'].get('video') for item in talk)
    assert any(item['config'].get('video') for item in textturn)
    assert any(item['config'].get('screen') for item in talk)
    assert any(item['config'].get('video') and item['config'].get('screen') for item in talk)
    assert any(item['config'].get('tools') == 'demo' for item in talk)
    assert any(item['id'] == 'talk-barge' for item in talk)
