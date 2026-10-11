from functools import lru_cache

import redis.asyncio as aioredis
from fastapi import HTTPException

from app.config import get_settings


@lru_cache
def get_redis() -> aioredis.Redis:
    return aioredis.from_url(get_settings().redis_url, decode_responses=True)


async def rate_limit(key: str, limit: int, window_s: int) -> None:
    """Fixed-window limiter shared across backend instances."""
    r = get_redis()
    bucket = f"rl:{key}"
    count = await r.incr(bucket)
    if count == 1:
        await r.expire(bucket, window_s)
    if count > limit:
        ttl = await r.ttl(bucket)
        raise HTTPException(status_code=429, detail="Too many requests", headers={"Retry-After": str(max(ttl, 1))})
