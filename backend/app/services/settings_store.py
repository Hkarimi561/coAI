"""Runtime settings editable by admins in the UI (stored in PostgreSQL, cached in Redis for 60s)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.config import get_settings
from app.db import SessionLocal
from app.models import AppSetting
from app.redis_client import get_redis

KEYS = ("web_search_enabled", "github_docs_enabled", "answer_cache_enabled")


def default(key: str) -> bool:
    s = get_settings()
    return {
        "web_search_enabled": s.websearch_provider.lower() != "none",
        "github_docs_enabled": s.github_docs_enabled,
        "answer_cache_enabled": s.answer_cache_enabled,
    }[key]


async def get_bool(key: str) -> bool:
    redis = get_redis()
    cached = await redis.get(f"appset:{key}")
    if cached is not None:
        return cached == "1"
    async with SessionLocal() as session:
        row = (await session.execute(select(AppSetting).where(AppSetting.key == key))).scalar_one_or_none()
    value = bool(row.value) if row is not None else default(key)
    await redis.set(f"appset:{key}", "1" if value else "0", ex=60)
    return value


async def get_all() -> dict[str, bool]:
    return {k: await get_bool(k) for k in KEYS}


async def set_bool(key: str, value: bool, user_id: uuid.UUID | None) -> None:
    if key not in KEYS:
        raise KeyError(key)
    stmt = pg_insert(AppSetting).values(key=key, value=value, updated_by=user_id, updated_at=datetime.now(UTC))
    stmt = stmt.on_conflict_do_update(
        index_elements=[AppSetting.key], set_={"value": value, "updated_by": user_id, "updated_at": datetime.now(UTC)}
    )
    async with SessionLocal() as session:
        await session.execute(stmt)
        await session.commit()
    await get_redis().delete(f"appset:{key}")
