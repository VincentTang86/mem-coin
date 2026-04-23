import orjson
import redis.asyncio as aioredis

from app.config import settings

HITS_CHANNEL = "hits"


async def publish_hit(payload: dict) -> None:
    r = aioredis.from_url(settings.redis_url)
    try:
        await r.publish(HITS_CHANNEL, orjson.dumps(payload).decode())
    finally:
        await r.aclose()
