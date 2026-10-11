"""Web search providers + durable cache (Redis -> PostgreSQL) + single-flight locking."""

import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any, Protocol

import httpx
from qdrant_client import models
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.config import get_settings
from app.db import SessionLocal
from app.models import WebCacheEntry
from app.redaction import redact
from app.redis_client import get_redis
from app.services.answer_cache import bump_kb_version
from app.services.container import get_embedder, get_vectorstore

log = logging.getLogger(__name__)

_RELEASE_LUA = "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end"


class WebSearchError(RuntimeError):
    pass


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


class SearchProvider(Protocol):
    name: str

    async def search(self, query: str, limit: int) -> list[SearchResult]: ...


class SearxngProvider:
    name = "searxng"

    def __init__(self) -> None:
        s = get_settings()
        self.base = s.searxng_url.rstrip("/")
        self.timeout = s.websearch_timeout_s

    async def search(self, query: str, limit: int) -> list[SearchResult]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(f"{self.base}/search", params={"q": query, "format": "json", "safesearch": 0})
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise WebSearchError(f"SearXNG request failed: {exc}") from exc
        out = []
        for r in resp.json().get("results", [])[:limit]:
            if r.get("url"):
                out.append(SearchResult(title=str(r.get("title", ""))[:200], url=r["url"], snippet=str(r.get("content", ""))[:700]))
        return out


class TavilyProvider:
    name = "tavily"

    def __init__(self) -> None:
        s = get_settings()
        if not s.tavily_api_key:
            raise WebSearchError("TAVILY_API_KEY is not set")
        self.key = s.tavily_api_key
        self.timeout = s.websearch_timeout_s

    async def search(self, query: str, limit: int) -> list[SearchResult]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    "https://api.tavily.com/search",
                    headers={"Authorization": f"Bearer {self.key}"},
                    json={"query": query, "max_results": limit, "search_depth": "basic"},
                )
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise WebSearchError(f"Tavily request failed: {exc}") from exc
        return [
            SearchResult(title=str(r.get("title", ""))[:200], url=r["url"], snippet=str(r.get("content", ""))[:700])
            for r in resp.json().get("results", [])[:limit]
            if r.get("url")
        ]


@dataclass
class CachedWeb:
    id: str
    cache_key: str
    query_text: str
    error_signature: str
    provider: str
    results: list[dict[str, Any]]
    answer: str | None
    created_at: str

    @classmethod
    def from_row(cls, row: WebCacheEntry) -> "CachedWeb":
        return cls(
            id=str(row.id),
            cache_key=row.cache_key,
            query_text=row.query_text,
            error_signature=row.error_signature,
            provider=row.provider,
            results=list(row.results or []),
            answer=row.answer,
            created_at=row.created_at.isoformat() if row.created_at else "",
        )

    def dumps(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def loads(cls, raw: str) -> "CachedWeb":
        return cls(**json.loads(raw))


class WebSearchService:
    def __init__(self) -> None:
        self.s = get_settings()
        self.redis = get_redis()
        self.provider: SearchProvider | None = None
        name = self.s.websearch_provider.lower()
        try:
            if name == "searxng":
                self.provider = SearxngProvider()
            elif name == "tavily":
                self.provider = TavilyProvider()
        except WebSearchError as exc:
            log.warning("Web search disabled: %s", exc)

    @property
    def enabled(self) -> bool:
        return self.provider is not None

    # -- cache ------------------------------------------------------------
    @staticmethod
    def _rkey(key: str) -> str:
        return f"webcache:{key}"

    async def lookup(self, key: str) -> CachedWeb | None:
        raw = await self.redis.get(self._rkey(key))
        if raw:
            return CachedWeb.loads(raw)
        now = datetime.now(UTC)
        async with SessionLocal() as session:
            row = (
                await session.execute(
                    select(WebCacheEntry).where(
                        WebCacheEntry.cache_key == key, WebCacheEntry.invalidated_at.is_(None), WebCacheEntry.expires_at > now
                    )
                )
            ).scalar_one_or_none()
        if row is None:
            return None
        entry = CachedWeb.from_row(row)
        remaining = max(int((row.expires_at - now).total_seconds()), 1)
        await self.redis.set(self._rkey(key), entry.dumps(), ex=min(remaining, 3600))
        return entry

    async def get_by_id(self, entry_id: str) -> CachedWeb | None:
        now = datetime.now(UTC)
        async with SessionLocal() as session:
            row = await session.get(WebCacheEntry, uuid.UUID(entry_id))
        if row is None or row.invalidated_at is not None or row.expires_at <= now:
            return None
        return CachedWeb.from_row(row)

    async def register_hit(self, entry_id: str) -> None:
        async with SessionLocal() as session:
            await session.execute(
                update(WebCacheEntry).where(WebCacheEntry.id == uuid.UUID(entry_id)).values(hit_count=WebCacheEntry.hit_count + 1)
            )
            await session.commit()

    async def set_answer(self, key: str, answer: str) -> None:
        async with SessionLocal() as session:
            await session.execute(update(WebCacheEntry).where(WebCacheEntry.cache_key == key).values(answer=answer))
            await session.commit()
        entry = await self.lookup(key)
        if entry:
            entry.answer = answer
            await self.redis.set(self._rkey(key), entry.dumps(), ex=3600)

    async def invalidate_key(self, key: str) -> None:
        """Drop a cache entry (used by an explicit user-requested re-search)."""
        async with SessionLocal() as session:
            await session.execute(
                update(WebCacheEntry).where(WebCacheEntry.cache_key == key).values(invalidated_at=datetime.now(UTC))
            )
            await session.commit()
        await self.redis.delete(self._rkey(key))
        try:
            await get_vectorstore().delete_where(kind="web", ref=f"web:{key}")
        except Exception:
            log.exception("Failed to remove cache vector for %s", key)

    async def invalidate(self, entry_id: uuid.UUID, admin_id: uuid.UUID) -> bool:
        async with SessionLocal() as session:
            row = await session.get(WebCacheEntry, entry_id)
            if row is None:
                return False
            row.invalidated_at = datetime.now(UTC)
            row.invalidated_by = admin_id
            await session.commit()
            key = row.cache_key
        await self.redis.delete(self._rkey(key))
        try:
            await get_vectorstore().delete_where(kind="web", ref=f"web:{key}")
        except Exception:
            log.exception("Failed to remove cache vector for %s", key)
        await bump_kb_version()
        return True

    async def _store(self, key: str, query: str, signature: str, results: list[SearchResult]) -> CachedWeb:
        assert self.provider is not None
        now = datetime.now(UTC)
        ttl = timedelta(hours=self.s.web_cache_ttl_hours if results else self.s.web_negative_ttl_hours)
        data = [asdict(r) for r in results]
        stmt = (
            pg_insert(WebCacheEntry)
            .values(
                cache_key=key, query_text=query, error_signature=signature, provider=self.provider.name,
                results=data, answer=None, hit_count=0, expires_at=now + ttl,
            )
            .on_conflict_do_update(
                index_elements=[WebCacheEntry.cache_key],
                set_={
                    "query_text": query, "error_signature": signature, "provider": self.provider.name, "results": data,
                    "answer": None, "expires_at": now + ttl, "invalidated_at": None, "invalidated_by": None, "created_at": now,
                },
            )
            .returning(WebCacheEntry)
        )
        async with SessionLocal() as session:
            row = (await session.execute(stmt)).scalar_one()
            await session.commit()
            entry = CachedWeb.from_row(row)
        await self.redis.set(self._rkey(key), entry.dumps(), ex=min(int(ttl.total_seconds()), 3600))
        if results:
            await self._index(entry)
        return entry

    async def _index(self, entry: CachedWeb) -> None:
        try:
            text = f"{entry.query_text}\n" + "\n".join(f"{r['title']}: {r['snippet']}" for r in entry.results[:5])
            [vec] = await get_embedder().embed([text[:3000]], "passage")
            store = get_vectorstore()
            await store.upsert(
                [
                    models.PointStruct(
                        id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"web:{entry.cache_key}")),
                        vector=vec,
                        payload={"kind": "web", "ref": f"web:{entry.cache_key}", "cache_id": entry.id, "cache_key": entry.cache_key,
                                 "query": entry.query_text},
                    )
                ]
            )
        except Exception:
            log.exception("Could not index web cache entry %s (semantic lookup disabled for it)", entry.cache_key)

    # -- single-flight search --------------------------------------------
    async def search(self, key: str, query: str, signature: str, refresh: bool = False) -> tuple[CachedWeb, str]:
        """Returns (entry, event) with event in cache_hit | coalesced | fresh.

        Exactly one concurrent caller performs the outbound request for a given key (Redis lock);
        the others poll the shared cache until the winner has stored the result.
        """
        if not self.provider:
            raise WebSearchError("Web search is not configured")
        if refresh:  # explicit user request: forget the cached research first, then search for real
            await self.invalidate_key(key)
        lock_key, err_key = f"sf:lock:{key}", f"sf:err:{key}"
        deadline = asyncio.get_running_loop().time() + self.s.single_flight_wait_s
        waited = False

        while True:
            entry = await self.lookup(key)
            if entry:
                return entry, ("coalesced" if waited else "cache_hit")
            if await self.redis.get(err_key):
                raise WebSearchError("A concurrent web search for this problem just failed; try again shortly")

            token = uuid.uuid4().hex
            if await self.redis.set(lock_key, token, nx=True, ex=self.s.single_flight_lock_ttl_s):
                try:
                    entry = await self.lookup(key)  # double-checked locking
                    if entry:
                        return entry, ("coalesced" if waited else "cache_hit")
                    try:
                        results = await self.provider.search(query, self.s.websearch_max_results)
                    except WebSearchError:
                        await self.redis.set(err_key, "1", ex=20)
                        raise
                    results = [
                        SearchResult(redact(r.title), r.url, redact(r.snippet)) for r in results
                    ]
                    return await self._store(key, query, signature, results), "fresh"
                finally:
                    await self.redis.eval(_RELEASE_LUA, 1, lock_key, token)

            waited = True
            if asyncio.get_running_loop().time() > deadline:
                raise WebSearchError("Timed out waiting for a concurrent web search")
            await asyncio.sleep(0.4)


@lru_cache
def get_websearch() -> WebSearchService:
    return WebSearchService()
