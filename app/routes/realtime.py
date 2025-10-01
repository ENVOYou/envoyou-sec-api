from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse, JSONResponse
from typing import AsyncIterator
import threading
import json
import queue
import asyncio
import time

from app.services.redis_service import redis_service
from app.utils.security import require_api_key

router = APIRouter()


def _sse_format(data: str, event: str | None = None) -> bytes:
    out = ''
    if event:
        out += f'event: {event}\n'
    for line in data.splitlines():
        out += f'data: {line}\n'
    out += '\n'
    return out.encode('utf-8')


def _fallback_generator() -> AsyncIterator[bytes]:
    async def gen():
        count = 0
        while True:
            await asyncio.sleep(2)
            count += 1
            payload = json.dumps({"timestamp": int(time.time() * 1000), "live_requests": count})
            yield _sse_format(payload)
    return gen()


@router.get("/", dependencies=[Depends(require_api_key)])
async def realtime_stream(request: Request):
    """
    Stream Server-Sent Events from Redis channel `live:requests`.
    Requires a valid API key (via Authorization Bearer, X-API-Key, or api_key query).
    """
    # If Redis not available, return a fallback synthetic stream
    if not redis_service.is_connected():
        return StreamingResponse(_fallback_generator(), media_type='text/event-stream')

    pubsub = redis_service.subscribe_to_channel('live:requests')
    if pubsub is None:
        return StreamingResponse(_fallback_generator(), media_type='text/event-stream')

    q: queue.Queue = queue.Queue()
    stop_event = threading.Event()

    def reader_thread():
        try:
            for message in pubsub.listen():
                if stop_event.is_set():
                    break
                if message is None:
                    continue
                # redis-py message dict has 'type' and 'data'
                try:
                    if message.get('type') == 'message':
                        data = message.get('data')
                        # ensure string
                        if isinstance(data, (bytes, bytearray)):
                            data = data.decode('utf-8')
                        if not isinstance(data, str):
                            data = json.dumps(data)
                        # If the publisher included a key_prefix, only queue if it matches the requester's prefix
                        try:
                            parsed = json.loads(data)
                        except Exception:
                            parsed = None

                        requester_key = getattr(request.state, 'api_key', None)
                        requester_prefix = requester_key[:8] if isinstance(requester_key, str) else None

                        if parsed and isinstance(parsed, dict) and parsed.get('key_prefix'):
                            if requester_prefix and parsed.get('key_prefix') == requester_prefix:
                                q.put(data)
                            else:
                                # not intended for this client
                                continue
                        else:
                            # no key scoping -> broadcast
                            q.put(data)
                except Exception:
                    # swallow to keep the reader alive
                    continue
        finally:
            try:
                pubsub.close()
            except Exception:
                pass

    thread = threading.Thread(target=reader_thread, daemon=True)
    thread.start()

    async def event_generator():
        try:
            loop = asyncio.get_running_loop()
            while True:
                if await request.is_disconnected():
                    break
                # block on queue.get in thread-pool to avoid blocking event loop
                item = await loop.run_in_executor(None, q.get)
                if item is None:
                    continue
                yield _sse_format(item)
        finally:
            stop_event.set()
            try:
                pubsub.close()
            except Exception:
                pass

    return StreamingResponse(event_generator(), media_type='text/event-stream')
