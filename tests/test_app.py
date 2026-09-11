from __future__ import annotations

from catalog import MODEL_TALK, MODEL_TRANSCRIBE, WORKSPACES


def test_home_and_static(client):
    home = client.get('/')
    assert home.status_code == 200
    assert '对话实验室' in home.text and 'id="workspaces"' in home.text
    assert 'data-page="talk"' in home.text and 'data-page="transcribe"' in home.text
    assert 'data-page="textturn"' in home.text
    assert 'id="compare-models"' in home.text
    assert 'id="session-limits"' in home.text
    assert '能撑多久' in home.text
    assert '不是万能' in home.text
    assert '1 对 1' in home.text
    css = client.get('/static/style.css')
    js = client.get('/static/app.js')
    assert css.status_code == 200 and js.status_code == 200
    assert '.camera-preview' in css.text
    assert 'object-fit:contain' in css.text
    assert 'sample.engine===active' in js.text
    assert '本页场景样例' in js.text
    assert '打开麦克风对话' in js.text
    assert '对着麦克风听写' in js.text
    assert '把样例送进去' not in js.text
    assert 'echoCancellation' in js.text
    assert 'isPlaying' in js.text
    assert 'barge-in' in js.text
    assert 'image/jpeg' in js.text
    assert '画中画' in js.text
    assert 'cellHtml' in js.text
    assert 'featureBlock' in js.text
    assert '开了会怎样' in js.text
    assert '.feature-block' in css.text
    assert 'drawPipFrame' in js.text
    assert 'pip-layer' in js.text
    assert '接着上次' in js.text
    assert 'Affective Dialog' in js.text
    assert "type:'text'" in js.text
    assert '再发一句' in js.text
    assert 'sendTypedTurn' in js.text
    assert 'grabJpeg' not in js.text
    assert '/api/speak' not in js.text


def test_catalog_and_docs(client):
    catalog = client.get('/api/catalog').json()
    assert catalog['checked'] == '2026-09-10'
    assert catalog['project_configured'] is False
    assert [item['id'] for item in catalog['workspaces']] == ['talk', 'transcribe', 'textturn']
    assert all(item.get('docs') and item.get('fit') and item.get('surface') and item.get('positioning') for item in catalog['workspaces'])
    talk = next(item for item in catalog['workspaces'] if item['id'] == 'talk')
    assert talk['model'] == MODEL_TALK
    assert 'camera' in talk['features'] and 'barge_in' in talk['features']
    assert 'screen' in talk['features'] and 'tools' in talk['features']
    assert 'session_resume' in talk['features']
    assert '1 对 1' in talk['positioning']['official']
    textturn = next(item for item in catalog['workspaces'] if item['id'] == 'textturn')
    assert 'camera' in textturn['features']
    assert 'barge_in' not in textturn['features']
    assert 'send_client_content' in textturn['positioning']['official']
    assert '长连接' in textturn['limit_note']
    assert all(item['url'].startswith('https://') for item in talk['docs'])
    transcribe = next(item for item in catalog['workspaces'] if item['id'] == 'transcribe')
    assert transcribe['model'] == MODEL_TRANSCRIBE
    assert 'cmn-Hans-CN' in transcribe['lead'] or any(lang['code'] == 'cmn-Hans-CN' for lang in transcribe['languages'])
    assert catalog['engine_locations']['talk'] == 'us-central1'
    assert catalog['engine_locations']['transcribe'] == 'global'
    samples = catalog['samples']
    assert len(samples) >= 10
    assert {item['engine'] for item in samples} == {'talk', 'transcribe', 'textturn'}
    assert catalog['feature_blurbs']['barge_in']['value']
    assert '接待' in catalog['feature_blurbs']['barge_in']['value']
    assert catalog['feature_blurbs']['camera']['caution']
    assert catalog['feature_value'][0] == ['功能 / 特性', '开了会怎样', '业务价值', '不要用来', '哪一页']
    assert catalog['api_out_of_demo'][0][1] == '业务价值'
    assert any('RAG' in row[0] for row in catalog['api_out_of_demo'])
    assert not any('Chirp' in row[0] or 'ADK' in row[0] or '双向视频' in row[0] or '出画面' in row[0] for row in catalog['api_out_of_demo'][1:])
    assert catalog['session_limits'][0][2] == '对业务意味着什么'
    assert any('打字页' in row[0] for row in catalog['session_limits'][1:])
    assert any('10 分钟' in row[1] and '打字' in row[0] for row in catalog['session_limits'][1:])
    assert talk.get('limit_impact') and '10 分钟' in talk['limit_impact']['items'][0]['impact']
    assert textturn.get('limit_impact') and '打字' in textturn['limit_impact']['lede']
    assert transcribe.get('limit_impact')
    js = client.get('/static/app.js')
    intro = js.text.split('function pageIntro')[1].split('function pageDocs')[0]
    assert 'htmlTable(catalog.session_limits)' not in intro
    assert 'limit_impact' in intro
    assert catalog['compare_models'][0][1] == '对话页'
    assert catalog['model_rules'][0][0] == '能力'
    for name in ('readme', 'guide', 'sources'):
        body = client.get(f'/api/doc/{name}').json()['text']
        assert 'Live' in body or 'live' in body
    assert client.get('/api/doc/missing').status_code == 404
    audio = client.get('/sample_assets/audio/welcome_cmn.wav')
    assert audio.status_code == 200
    assert audio.content[:4] == b'RIFF'
    assert WORKSPACES[0]['id'] == 'talk'


def test_preview_ok_and_validation(client):
    ok = client.post('/api/preview', json={
        'engine': 'talk', 'model': MODEL_TALK, 'language': '', 'voice': 'Kore',
        'system_instruction': '用普通话回答',
    })
    assert ok.status_code == 200
    body = ok.json()
    assert body['api'] == 'live'
    assert body['model'] == MODEL_TALK
    assert body['location'] == 'us-central1'
    assert body['request']['setup']['response_modalities'][0] == 'AUDIO'
    assert 'BidiGenerateContent' in body['endpoint']

    cap = client.post('/api/preview', json={
        'engine': 'transcribe', 'model': MODEL_TRANSCRIBE, 'language': 'cmn-Hans-CN',
    })
    assert cap.status_code == 200
    cap_body = cap.json()
    assert cap_body['location'] == 'global'
    assert cap_body['request']['setup']['response_modalities'] == ['TEXT']
    assert cap_body['language_codes'] == ['cmn-Hans-CN']

    auto = client.post('/api/preview', json={
        'engine': 'transcribe', 'model': MODEL_TRANSCRIBE, 'language': 'auto',
    })
    assert auto.status_code == 200
    assert auto.json()['language_codes'] == []

    wrong_model = client.post('/api/preview', json={
        'engine': 'talk', 'model': MODEL_TRANSCRIBE, 'voice': 'Kore',
    })
    assert wrong_model.status_code == 400

    mandarin_speech = client.post('/api/preview', json={
        'engine': 'talk', 'model': MODEL_TALK, 'language': 'cmn-Hans-CN', 'voice': 'Kore',
    })
    assert mandarin_speech.status_code == 400

    speak_empty = client.post('/api/preview', json={
        'engine': 'textturn', 'model': MODEL_TALK, 'voice': 'Kore', 'text': '',
    })
    assert speak_empty.status_code == 400

    speak = client.post('/api/preview', json={
        'engine': 'textturn', 'model': MODEL_TALK, 'voice': 'Puck', 'text': 'hello', 'language': 'en-US',
    })
    assert speak.status_code == 200
    assert speak.json()['location'] == 'us-central1'

    live_call = client.post('/api/speak', json={
        'engine': 'textturn', 'model': MODEL_TALK, 'voice': 'Kore', 'text': 'hello',
    })
    assert live_call.status_code == 400
