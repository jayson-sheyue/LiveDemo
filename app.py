"""Live demo. Local: uvicorn app:app --host 127.0.0.1 --port 8003. Cloud Run: Procfile / K_SERVICE."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request as WebRequest, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from catalog import (
    API_OUT_OF_DEMO, CHECKED, COMPARE_API, COMPARE_METHODS, COMPARE_MODELS, DOCS, ENGINE_LOCATIONS,
    FEATURE_BLURBS, FEATURE_VALUE, FIT_GUIDE, MODEL_CARDS, MODEL_RULES, MODELS, SESSION_LIMITS, VOICES, WHY_NOT_LIVE, WORKSPACES,
)
from live import (
    Request, UserError, adc_available, configure_live_proxy, error_payload,
    iter_session_events, plan, require_auth, speak_turn,
)
from samples import load_samples, sample_audio_path

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
SAMPLES = load_samples()
SAMPLE_INDEX = {item['id']: item for item in SAMPLES}
configure_live_proxy()


def allowed_hosts() -> list[str]:
    """Local loopback by default; Cloud Run (K_SERVICE) also allows *.run.app; optional ALLOWED_HOSTS."""
    hosts = ['localhost', '127.0.0.1', '[::1]', 'testserver']
    if os.getenv('K_SERVICE'):
        hosts.append('*.run.app')
    for item in os.getenv('ALLOWED_HOSTS', '').split(','):
        host = item.strip()
        if host and host not in hosts:
            hosts.append(host)
    return hosts


def bind_host_port(default_port: str = '8003') -> tuple[str, int]:
    if os.getenv('K_SERVICE'):
        return '0.0.0.0', int(os.getenv('PORT') or '8080')
    return '127.0.0.1', int(os.getenv('DEMO_PORT') or default_port)


def same_origin(origin: str, request: WebRequest) -> bool:
    """Allow same-page POSTs. Cloud Run may rewrite scheme/host vs browser Origin."""
    from urllib.parse import urlparse
    parsed = urlparse(origin)
    if not parsed.netloc:
        return False
    candidates = {
        request.headers.get('x-forwarded-host', '').split(',')[0].strip(),
        request.headers.get('host', '').strip(),
        request.url.hostname or '',
        urlparse(str(request.base_url)).netloc,
    }
    if parsed.netloc in {item for item in candidates if item}:
        return True
    # Cloud Run serves two hostnames per service; Origin/Host can disagree.
    if os.getenv('K_SERVICE'):
        origin_host = (parsed.hostname or '').lower()
        req_host = (request.headers.get('host') or '').split(':')[0].lower()
        if origin_host.endswith('.run.app') and req_host.endswith('.run.app'):
            return True
    return False


app = FastAPI(title='对话实验室', description='Gemini Live API · 本地教学 Demo')
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts())
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')
session_lock = asyncio.Lock()
MAX_BODY = 10_000_000


@app.middleware('http')
async def local_only(request: WebRequest, call_next):
    if request.method == 'POST':
        origin = request.headers.get('origin')
        if origin and not same_origin(origin, request):
            return JSONResponse({'detail': '请从本 Demo 页面发起请求。'}, status_code=403)
        if request.headers.get('content-type', '').split(';')[0] != 'application/json':
            return JSONResponse({'detail': '需要 JSON 请求。'}, status_code=415)
        body = await request.body()
        if len(body) > MAX_BODY:
            return JSONResponse({'detail': '请求过大。请使用短文本或短音频。'}, status_code=413)
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@app.exception_handler(RequestValidationError)
async def invalid_request(request, exc):
    return JSONResponse({'detail': '输入格式或长度不正确，请检查文字、声音和音频。'}, status_code=422)


@app.get('/')
def home():
    return FileResponse(ROOT / 'static' / 'index.html')


@app.get('/api/catalog')
def catalog():
    return {
        'voices': VOICES,
        'models': MODELS,
        'model_cards': MODEL_CARDS,
        'workspaces': WORKSPACES,
        'samples': SAMPLES,
        'compare_models': COMPARE_MODELS,
        'compare_methods': COMPARE_METHODS,
        'compare_api': COMPARE_API,
        'why_not_live': WHY_NOT_LIVE,
        'fit_guide': FIT_GUIDE,
        'session_limits': SESSION_LIMITS,
        'feature_value': FEATURE_VALUE,
        'feature_blurbs': FEATURE_BLURBS,
        'api_out_of_demo': API_OUT_OF_DEMO,
        'model_rules': MODEL_RULES,
        'docs': DOCS,
        'checked': CHECKED,
        'project_configured': bool(os.getenv('GOOGLE_CLOUD_PROJECT')),
        'adc_configured': adc_available(),
        'engine_locations': ENGINE_LOCATIONS,
        'location_raw': os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1'),
    }


@app.get('/api/doc/{name}')
def document(name: str):
    files = {'readme': 'README.md', 'guide': 'learning_guide.md', 'sources': 'docs/official_sources.md'}
    if name not in files:
        raise HTTPException(404)
    path = ROOT / files[name]
    if not path.is_file():
        raise HTTPException(404)
    return {'text': path.read_text(encoding='utf-8')}


@app.get('/sample_assets/audio/{name}')
def sample_file(name: str):
    if '/' in name or '\\' in name or name.startswith('.'):
        raise HTTPException(404)
    path = ROOT / 'sample_assets' / 'audio' / name
    if not path.is_file():
        raise HTTPException(404)
    return FileResponse(path)


def resolve_audio(r: Request) -> bytes | None:
    if r.sample_id:
        item = SAMPLE_INDEX.get(r.sample_id)
        if not item:
            raise UserError('找不到这个样例。')
        path = sample_audio_path(r.sample_id)
        if not path:
            return None
        return path.read_bytes()
    if r.audio_b64:
        from live import decode_audio
        return decode_audio(r)
    return None


@app.post('/api/preview')
def preview_route(r: Request):
    try:
        audio = None
        if r.sample_id or r.audio_b64:
            audio = resolve_audio(r)
        return plan(r, audio)
    except UserError as error:
        raise HTTPException(400, str(error)) from None


@app.post('/api/speak')
async def speak_route(r: Request):
    try:
        r.engine = 'textturn'
        require_auth()
        planned = plan(r)
    except UserError as error:
        raise HTTPException(400, str(error)) from None
    if session_lock.locked():
        raise HTTPException(409, '已有 Live 会话运行中，请完成或停止后再试。')
    async with session_lock:
        try:
            result = await speak_turn(r)
            result['plan'] = {key: planned[key] for key in ('api', 'model', 'location', 'warnings')}
            expected = SAMPLE_INDEX.get(r.sample_id, {}).get('expected')
            if expected:
                result['expected'] = expected
            return result
        except UserError as error:
            raise HTTPException(400, str(error)) from None
        except Exception as error:
            payload = error_payload(error)
            print(f'[speak] {payload["error_type"]}: {error}', flush=True)
            raise HTTPException(400, payload) from None


@app.websocket('/ws/live')
async def live_route(socket: WebSocket):
    await socket.accept()
    if session_lock.locked():
        await socket.send_json({'type': 'error', 'message': '已有 Live 会话运行中。'})
        await socket.close()
        return
    queue: asyncio.Queue[bytes | dict | None] = asyncio.Queue()
    await session_lock.acquire()
    try:
        first = await socket.receive()
        if 'text' not in first:
            await socket.send_json({'type': 'error', 'message': '请先发送 JSON 配置。'})
            return
        r = Request.model_validate_json(first['text'])
        require_auth()
        plan(r)

        async def incoming():
            while True:
                item = await queue.get()
                yield item
                if item is None:
                    break

        async def reader():
            try:
                while True:
                    message = await socket.receive()
                    if message.get('type') == 'websocket.disconnect':
                        break
                    if message.get('bytes') is not None:
                        await queue.put(message['bytes'])
                    elif message.get('text'):
                        data = json.loads(message['text'])
                        kind = data.get('type')
                        if kind == 'stop':
                            break
                        await queue.put(data)
            except WebSocketDisconnect:
                pass
            await queue.put(None)

        reader_task = asyncio.create_task(reader())

        async def forward():
            async for event in iter_session_events(r, incoming()):
                await socket.send_json(event)

        forward_task = asyncio.create_task(forward())
        ended_ok = False
        try:
            await asyncio.wait([reader_task, forward_task], return_when=asyncio.FIRST_COMPLETED)
            if forward_task.done() and not forward_task.cancelled():
                error = forward_task.exception()
                if error:
                    raise error
            ended_ok = True
        finally:
            await queue.put(None)
            for task in (reader_task, forward_task):
                if task is None:
                    continue
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
            if ended_ok:
                try:
                    await socket.send_json({'type': 'done'})
                except Exception:
                    pass
    except UserError as error:
        try:
            await socket.send_json({'type': 'error', 'message': str(error)})
        except Exception:
            pass
    except Exception as error:
        payload = error_payload(error)
        print(f'[live] {payload["error_type"]}: {error}', flush=True)
        try:
            await socket.send_json({'type': 'error', **payload})
        except Exception:
            pass
    finally:
        if session_lock.locked():
            session_lock.release()
        try:
            await socket.close()
        except Exception:
            pass


if __name__ == '__main__':
    import uvicorn
    host, port = bind_host_port('8003')
    uvicorn.run('app:app', host=host, port=port, reload=False)
