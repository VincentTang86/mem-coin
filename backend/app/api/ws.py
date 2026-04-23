import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis

from app.config import settings
from app.tasks.publisher import HITS_CHANNEL

log = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/live")
async def ws_live(ws: WebSocket):
    await ws.accept()
    r = aioredis.from_url(settings.redis_url)
    pubsub = r.pubsub()
    await pubsub.subscribe(HITS_CHANNEL)

    async def pump():
        async for msg in pubsub.listen():
            if msg.get("type") != "message":
                continue
            data = msg["data"]
            if isinstance(data, bytes):
                data = data.decode()
            await ws.send_text(data)

    try:
        pump_task = asyncio.create_task(pump())
        # keep the connection alive; client can send pings
        while True:
            try:
                await ws.receive_text()
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    finally:
        pump_task.cancel()
        try:
            await pubsub.unsubscribe(HITS_CHANNEL)
        except Exception:
            pass
        await pubsub.close()
        await r.aclose()
