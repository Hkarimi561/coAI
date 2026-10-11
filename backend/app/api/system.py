"""Live status of every dependency the assistant needs (shown in the UI header and on the admin status page)."""

import asyncio
from typing import Any

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text

from app.config import get_settings
from app.db import SessionLocal
from app.models import Document, User
from app.redaction import redact
from app.redis_client import get_redis
from app.security import get_current_user
from app.services import settings_store
from app.services.ci import get_ci
from app.services.container import get_embedder, get_llm, get_vectorstore
from app.services.docker_inspector import DockerError, get_docker
from app.services.websearch import get_websearch

router = APIRouter(prefix="/system", tags=["system"])


async def _safe(coro: Any, timeout: float = 8) -> tuple[bool | None, str]:
    try:
        return await asyncio.wait_for(coro, timeout)
    except TimeoutError:
        return False, "timed out"
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


async def _postgres() -> tuple[bool, str]:
    async with SessionLocal() as s:
        await s.execute(text("select 1"))
    return True, "connected"


async def _redis() -> tuple[bool, str]:
    return bool(await get_redis().ping()), "connected"


async def _qdrant() -> tuple[bool, str]:
    ok = await get_vectorstore().health()
    return ok, "connected" if ok else "cannot reach Qdrant"


async def _embeddings() -> tuple[bool | None, str]:
    emb = get_embedder()
    emb.warmup()
    state = emb.state()
    s = get_settings()
    label = f"{s.embedding_provider}:{s.embedding_model}"
    if state == "ready":
        return True, label
    if state == "loading":
        return None, f"{label} - loading / downloading the model, please wait"
    return False, f"{label} - {emb.error}"


async def _llm() -> tuple[bool, str]:
    return await get_llm().health()


async def _web() -> tuple[bool | None, str]:
    s = get_settings()
    ws = get_websearch()
    web_on = ws.web_provider is not None and await settings_store.get_bool("web_search_enabled")
    gh_on = await settings_store.get_bool("github_docs_enabled")
    if not web_on and not gh_on:
        return None, "disabled (admin settings or WEBSEARCH_PROVIDER=none)"
    if not web_on:
        return True, "web search off - GitHub project docs only"
    if s.websearch_provider == "searxng":
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(f"{s.searxng_url.rstrip('/')}/healthz")
        except httpx.HTTPError as exc:
            return False, f"searxng unreachable ({type(exc).__name__})"
        return (True, f"searxng @ {s.searxng_url}") if r.status_code < 400 else (False, f"searxng HTTP {r.status_code}")
    return True, f"{s.websearch_provider} configured"


async def _docker() -> tuple[bool | None, str]:
    d = get_docker()
    if not d.enabled:
        return None, "disabled (DOCKER_ALLOWED_CONTAINERS is empty)"
    try:
        names = await d.allowed_names()
    except DockerError as exc:
        return False, str(exc)
    return True, f"{len(names)} allowed container(s) visible"


async def _ci() -> tuple[bool | None, str]:
    ci = get_ci()
    return (True, f"{ci.name} configured") if ci.configured else (None, "not configured")


@router.get("/status")
async def status(user: User = Depends(get_current_user)) -> dict[str, Any]:
    names = ["llm", "embeddings", "qdrant", "postgres", "redis", "web_search", "docker", "ci"]
    results = await asyncio.gather(
        _safe(_llm()), _safe(_embeddings(), 5), _safe(_qdrant()), _safe(_postgres()), _safe(_redis()),
        _safe(_web()), _safe(_docker()), _safe(_ci()),
    )
    admin = user.role == "admin"
    comps = {n: {"ok": ok, "detail": redact(detail) if admin else ""} for n, (ok, detail) in zip(names, results, strict=True)}
    out: dict[str, Any] = {"components": comps, "assistant_ready": bool(comps["llm"]["ok"] and comps["embeddings"]["ok"])}
    if admin:
        try:
            async with SessionLocal() as s:
                rows = (await s.execute(select(Document.status, func.count()).group_by(Document.status))).all()
            out["documents"] = {st: n for st, n in rows}
        except Exception:  # noqa: BLE001
            out["documents"] = {}
    return out
