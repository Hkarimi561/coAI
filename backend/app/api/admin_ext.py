"""Admin API for MCP servers (tool allow-list) and skills (playbooks)."""

import re
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import McpServer, Skill
from app.redaction import redact
from app.security import require_any_permission, require_permission
from app.services import gaps as gaps_svc, mcp_client, skills as skills_svc
from app.services.answer_cache import bump_kb_version

router = APIRouter(prefix="/admin", tags=["admin"])

_SLUG = re.compile(r"^[a-z0-9][a-z0-9_-]{0,47}$")


def _root_error(exc: BaseException) -> str:
    while isinstance(exc, BaseExceptionGroup) and exc.exceptions:
        exc = exc.exceptions[0]
    return redact(f"{type(exc).__name__}: {exc}")[:500]


# ---------------------------------------------------------------- MCP servers
class McpIn(BaseModel):
    name: str = Field(min_length=1, max_length=48)
    transport: Literal["http", "sse"] = "http"
    url: str = Field(min_length=8, max_length=500)
    headers: dict[str, str] = Field(default_factory=dict)
    description: str = Field(default="", max_length=200)
    forward_user: bool = False
    enabled: bool = True


class McpUpdate(BaseModel):
    transport: Literal["http", "sse"] | None = None
    url: str | None = Field(default=None, min_length=8, max_length=500)
    headers: dict[str, str] | None = None  # replaces all headers when given
    description: str | None = Field(default=None, max_length=200)
    forward_user: bool | None = None
    enabled: bool | None = None


class McpToolsIn(BaseModel):
    enabled_tools: list[str]


def _mcp_out(s: McpServer) -> dict[str, Any]:
    return {
        "id": str(s.id), "name": s.name, "description": s.description or "", "transport": s.transport, "url": s.url, "header_names": sorted((s.headers or {}).keys()),
        "enabled": s.enabled, "forward_user": s.forward_user,
        "tools": [{"name": t["name"], "description": t.get("description", ""), "destructive": bool(t.get("destructive"))} for t in s.tools or []],
        "enabled_tools": s.enabled_tools or [], "last_error": s.last_error, "synced_at": s.synced_at.isoformat() if s.synced_at else None,
    }


def _check_url(url: str) -> str:
    url = url.strip()
    if not re.match(r"^https?://", url):
        raise HTTPException(422, "URL must start with http:// or https://")
    return url


async def _server(session: AsyncSession, server_id: uuid.UUID) -> McpServer:
    s = await session.get(McpServer, server_id)
    if s is None:
        raise HTTPException(404, "MCP server not found")
    return s


@router.get("/mcp", dependencies=[Depends(require_permission("mcp.manage"))])
async def list_mcp(session: AsyncSession = Depends(get_session)) -> list[dict[str, Any]]:
    rows = (await session.execute(select(McpServer).order_by(McpServer.name))).scalars().all()
    return [_mcp_out(s) for s in rows]


@router.post("/mcp", status_code=201, dependencies=[Depends(require_permission("mcp.manage"))])
async def create_mcp(body: McpIn, session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    name = body.name.strip().lower()
    if not _SLUG.match(name):
        raise HTTPException(422, "Name must be lowercase letters, digits, '-' or '_' (max 48)")
    s = McpServer(name=name, transport=body.transport, url=_check_url(body.url), headers=body.headers, description=body.description.strip(), forward_user=body.forward_user, enabled=body.enabled,
                  tools=[], enabled_tools=[])
    session.add(s)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(409, "A server with this name already exists") from exc
    mcp_client.invalidate()
    return _mcp_out(s)


@router.put("/mcp/{server_id}", dependencies=[Depends(require_permission("mcp.manage"))])
async def update_mcp(server_id: uuid.UUID, body: McpUpdate, session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    s = await _server(session, server_id)
    if body.transport is not None:
        s.transport = body.transport
    if body.url is not None:
        s.url = _check_url(body.url)
    if body.headers is not None:
        s.headers = body.headers
    if body.description is not None:
        s.description = body.description.strip()
    if body.forward_user is not None:
        s.forward_user = body.forward_user
    if body.enabled is not None:
        s.enabled = body.enabled
    await session.commit()
    mcp_client.invalidate()
    return _mcp_out(s)


@router.post("/mcp/{server_id}/sync", dependencies=[Depends(require_permission("mcp.manage"))])
async def sync_mcp(server_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    """Connects to the server and refreshes its tool list. New tools stay disabled until an admin allows them."""
    s = await _server(session, server_id)
    try:
        tools = await mcp_client.discover(s)
    except BaseException as exc:  # noqa: BLE001 - ExceptionGroup from the transport task group
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        s.last_error = _root_error(exc)
        await session.commit()
        mcp_client.invalidate()
        return _mcp_out(s)
    s.tools = tools
    names = {t["name"] for t in tools}
    s.enabled_tools = [t for t in s.enabled_tools or [] if t in names]
    s.last_error, s.synced_at = None, datetime.now(UTC)
    await session.commit()
    mcp_client.invalidate()
    return _mcp_out(s)


@router.put("/mcp/{server_id}/tools", dependencies=[Depends(require_permission("mcp.manage"))])
async def set_mcp_tools(server_id: uuid.UUID, body: McpToolsIn, session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    s = await _server(session, server_id)
    known = {t["name"] for t in s.tools or []}
    s.enabled_tools = sorted(t for t in set(body.enabled_tools) if t in known)
    await session.commit()
    mcp_client.invalidate()
    return _mcp_out(s)


@router.delete("/mcp/{server_id}", status_code=204, dependencies=[Depends(require_permission("mcp.manage"))])
async def delete_mcp(server_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> None:
    s = await _server(session, server_id)
    await session.delete(s)
    await session.commit()
    mcp_client.invalidate()


# ---------------------------------------------------------------- skills
class SkillIn(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    description: str = Field(min_length=10, max_length=1000)
    instructions: str = Field(min_length=10, max_length=20000)
    enabled: bool = True


def _skill_out(s: Skill) -> dict[str, Any]:
    return {"id": str(s.id), "name": s.name, "description": s.description, "instructions": s.instructions, "enabled": s.enabled,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None}


async def _index(skill: Skill) -> None:
    try:
        await skills_svc.index_skill(skill)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Skill saved but indexing failed: {redact(str(exc))[:200]}") from exc
    await bump_kb_version()  # cached answers may predate this skill


@router.get("/skills", dependencies=[Depends(require_permission("skills.manage"))])
async def list_skills(session: AsyncSession = Depends(get_session)) -> list[dict[str, Any]]:
    rows = (await session.execute(select(Skill).order_by(Skill.name))).scalars().all()
    return [_skill_out(s) for s in rows]


@router.post("/skills", status_code=201, dependencies=[Depends(require_permission("skills.manage"))])
async def create_skill(body: SkillIn, session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    s = Skill(name=body.name.strip(), description=body.description.strip(), instructions=body.instructions.strip(), enabled=body.enabled)
    session.add(s)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(409, "A skill with this name already exists") from exc
    await session.refresh(s)
    await _index(s)
    return _skill_out(s)


@router.put("/skills/{skill_id}", dependencies=[Depends(require_permission("skills.manage"))])
async def update_skill(skill_id: uuid.UUID, body: SkillIn, session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    s = await session.get(Skill, skill_id)
    if s is None:
        raise HTTPException(404, "Skill not found")
    s.name, s.description, s.instructions, s.enabled = body.name.strip(), body.description.strip(), body.instructions.strip(), body.enabled
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(409, "A skill with this name already exists") from exc
    await session.refresh(s)
    await _index(s)
    return _skill_out(s)


@router.delete("/skills/{skill_id}", status_code=204, dependencies=[Depends(require_permission("skills.manage"))])
async def delete_skill(skill_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> None:
    s = await session.get(Skill, skill_id)
    if s is None:
        raise HTTPException(404, "Skill not found")
    await session.delete(s)
    await session.commit()
    await skills_svc.remove_skill(skill_id)
    await bump_kb_version()


# ---------------------------------------------------------------- knowledge-gap report
@router.get("/gaps", dependencies=[Depends(require_permission("gaps.view"))])
async def knowledge_gaps(days: int = Query(default=7, ge=1, le=90), session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    """Questions the assistant could not answer well, clustered by topic."""
    return await gaps_svc.compute(session, days)


@router.get("/gaps/export", dependencies=[Depends(require_permission("gaps.view"))])
async def knowledge_gaps_export(days: int = Query(default=7, ge=1, le=90), session: AsyncSession = Depends(get_session)) -> Response:
    report = await gaps_svc.compute(session, days)
    name = f"knowledge-gaps-{datetime.now(UTC):%Y-%m-%d}.md"
    return Response(gaps_svc.to_markdown(report), media_type="text/markdown; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{name}"'})


# ---------------------------------------------------------------- dashboard overview (sidebar badges + home cards)
@router.get("/overview", dependencies=[Depends(require_any_permission)])
async def admin_overview(session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    """Counts for the admin dashboard and the sidebar badges."""
    from sqlalchemy import func

    from app.models import Conversation, Document, Lesson, User, WebCacheEntry

    async def one(stmt: Any) -> int:
        return int((await session.execute(stmt)).scalar() or 0)

    docs = int(await one(select(func.count()).select_from(Document)))
    chunks = await one(select(func.coalesce(func.sum(Document.chunk_count), 0)))
    doc_errors = await one(select(func.count()).select_from(Document).where(Document.status != "indexed"))
    servers = (await session.execute(select(McpServer))).scalars().all()
    return {
        "documents": {"count": docs, "chunks": chunks, "errors": doc_errors},
        "skills": {"total": await one(select(func.count()).select_from(Skill)), "enabled": await one(select(func.count()).select_from(Skill).where(Skill.enabled.is_(True)))},
        "mcp": {
            "servers": len(servers), "enabled": sum(1 for s in servers if s.enabled),
            "tools_enabled": sum(len(s.enabled_tools or []) for s in servers if s.enabled), "tools_total": sum(len(s.tools or []) for s in servers),
        },
        "lessons_pending": await one(select(func.count()).select_from(Lesson).where(Lesson.status == "pending")),
        "conversations": {
            "total": await one(select(func.count()).select_from(Conversation)),
            "pending_review": await one(select(func.count()).select_from(Conversation).where(Conversation.status == "pending_review")),
        },
        "users": await one(select(func.count()).select_from(User)),
        "cache_entries": await one(select(func.count()).select_from(WebCacheEntry)),
    }
