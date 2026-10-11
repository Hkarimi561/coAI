"""Chat answer cache: a repeated question is answered instantly from a previous grounded answer.

Entries live in Redis (AOF-persisted in docker-compose) and are keyed by the normalised question signature plus a
knowledge-base version. The version is bumped whenever documents, confirmed solutions or web-cache entries change,
which invalidates every cached answer at once (they may no longer reflect the best sources).
"""

import hashlib
import json
from typing import Any

from app.config import get_settings
from app.redis_client import get_redis

_VERSION_KEY = "anscache:kbver"


async def bump_kb_version() -> None:
    await get_redis().incr(_VERSION_KEY)


async def make_key(signature_key: str, web_only: bool) -> str:
    version = await get_redis().get(_VERSION_KEY) or "0"
    digest = hashlib.sha256(f"{version}|{signature_key}|{int(web_only)}".encode()).hexdigest()[:40]
    return f"anscache:{digest}"


async def get(key: str) -> dict[str, Any] | None:
    raw = await get_redis().get(key)
    return json.loads(raw) if raw else None


async def put(key: str, data: dict[str, Any]) -> None:
    await get_redis().set(key, json.dumps(data, ensure_ascii=False), ex=get_settings().answer_cache_ttl_hours * 3600)


async def delete(key: str | None) -> None:
    if key:
        await get_redis().delete(key)
