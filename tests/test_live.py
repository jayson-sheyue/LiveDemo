from __future__ import annotations

import os

from catalog import MODEL_TALK, MODEL_TRANSCRIBE
from live import Request, UserError, error_message, location_for, merge_transcript, parse_live_message, plan


def test_talk_rewrites_global_location():
    os.environ['GOOGLE_CLOUD_LOCATION'] = 'global'
    try:
        planned = plan(Request(engine='talk', model=MODEL_TALK, voice='Kore', language=''))
        assert planned['location'] == 'us-central1'
        assert any('global' in item for item in planned['warnings'])
    finally:
        os.environ['GOOGLE_CLOUD_LOCATION'] = 'us-central1'


def test_transcribe_rewrites_regional_location():
    os.environ['GOOGLE_CLOUD_LOCATION'] = 'us-central1'
    planned = plan(Request(engine='transcribe', model=MODEL_TRANSCRIBE, language='en-US'))
    assert planned['location'] == 'global'
    assert planned['request']['setup']['response_modalities'] == ['TEXT']
    assert 'Chirp' in ' '.join(planned['warnings']) or 'StreamingRecognize' in ' '.join(planned['warnings'])


def test_native_rejects_mandarin_speech_config():
    try:
        plan(Request(engine='textturn', model=MODEL_TALK, language='cmn-Hans-CN', text='你好', voice='Kore'))
        raise AssertionError('should reject')
    except UserError as error:
        assert '普通话' in str(error)


def test_transcribe_rejects_talk_model():
    try:
        plan(Request(engine='transcribe', model=MODEL_TALK, language='en-US'))
        raise AssertionError('should reject')
    except UserError as error:
        assert 'gemini-3.5-transcribe-live-preview' in str(error)


def test_socks_error_is_not_timeout():
    text = error_message(ImportError('connecting through a SOCKS proxy requires python-socks'))
    assert 'SOCKS' in text
    assert '10 分钟' not in text


def test_turn_coverage_error_is_not_modality():
    text = error_message(RuntimeError(
        "Invalid value at 'setup.realtime_input_config.turn_coverage' (1007)"
    ))
    assert 'turn_coverage' in text or 'JPEG' in text
    assert 'AUDIO' not in text


def test_talk_barge_in_and_video_preview():
    barge = plan(Request(engine='talk', model=MODEL_TALK, voice='Kore', language='', barge_in=True))
    assert barge['request']['setup']['realtime_input_config']['activity_handling'] == 'START_OF_ACTIVITY_INTERRUPTS'
    quiet = plan(Request(engine='talk', model=MODEL_TALK, voice='Kore', language='', barge_in=False))
    assert quiet['request']['setup']['realtime_input_config']['activity_handling'] == 'NO_INTERRUPTION'
    cam = plan(Request(engine='talk', model=MODEL_TALK, voice='Kore', language='', video=True))
    assert 'turn_coverage' not in cam['request']['setup'].get('realtime_input_config', {})
    assert any('JPEG' in item or '2 分钟' in item for item in cam['warnings'])
    typed = plan(Request(engine='textturn', model=MODEL_TALK, voice='Kore', language='', text='看见什么', video=True))
    assert 'realtime_input_config' not in typed['request']['setup']
    off = plan(Request(engine='talk', model=MODEL_TALK, voice='Kore', language='', barge_in=False))
    assert any('关闭打断' in item for item in off['warnings'])
    try:
        plan(Request(engine='transcribe', model=MODEL_TRANSCRIBE, language='en-US', video=True))
        raise AssertionError('should reject')
    except UserError as error:
        assert '摄像头' in str(error)
    loc, warnings = location_for(Request(engine='talk', model=MODEL_TALK, location='mars'))
    assert loc == 'us-central1'
    assert warnings


def test_session_options_preview():
    resume = plan(Request(engine='talk', model=MODEL_TALK, voice='Kore', language='', session_resume=True))
    assert 'session_resumption' in resume['request']['setup']
    compress = plan(Request(engine='talk', model=MODEL_TALK, voice='Kore', language='', compress=True, video=True))
    assert compress['request']['setup']['context_window_compression']['trigger_tokens'] == 50000
    tools = plan(Request(engine='talk', model=MODEL_TALK, voice='Kore', language='', tools='demo'))
    assert tools['request']['setup']['tools'][0]['function_declarations'][0]['name'] == 'get_current_time'
    search = plan(Request(engine='talk', model=MODEL_TALK, voice='Kore', language='', tools='search'))
    assert 'google_search' in search['request']['setup']['tools'][0]
    native = plan(Request(
        engine='talk', model=MODEL_TALK, voice='Kore', language='', affective=True, proactive=True,
    ))
    assert native['request']['setup']['enable_affective_dialog'] is True
    assert native['request']['setup']['proactivity']['proactive_audio'] is True
    screen = plan(Request(engine='talk', model=MODEL_TALK, voice='Kore', language='', screen=True))
    assert any('屏幕' in item or 'JPEG' in item for item in screen['warnings'])
    pip = plan(Request(engine='talk', model=MODEL_TALK, voice='Kore', language='', video=True, screen=True))
    assert any('画中画' in item for item in pip['warnings'])
    try:
        plan(Request(engine='transcribe', model=MODEL_TRANSCRIBE, language='en-US', tools='demo'))
        raise AssertionError('should reject')
    except UserError as error:
        assert '听写' in str(error) or '函数' in str(error)


class _Obj:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_parse_does_not_duplicate_pcm():
    pcm = b'\x01\x00' * 8
    part = _Obj(inline_data=_Obj(data=pcm), text=None)
    sc = _Obj(
        interrupted=False, turn_complete=False, generation_complete=False,
        model_turn=_Obj(parts=[part]),
        interim_input_transcription=None, input_transcription=None, output_transcription=None,
    )
    event = parse_live_message(_Obj(setup_complete=None, go_away=None, data=pcm, server_content=sc))
    assert event['audio'] == pcm


def test_merge_transcript_prefers_growing_prefix():
    assert merge_transcript(['你', '你好', '你好呀']) == '你好呀'
    assert merge_transcript(['Hello', ' world']) == 'Hello world'
