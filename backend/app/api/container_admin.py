"""Admin: who may see / read logs / act on which container, plus the audit trail."""

import re
import uuid
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import ContainerAudit, ContainerGrant, User
from app.security import require_admin
from app.services.docker_inspector import DockerError, get_docker

router = APIRouter(prefix="/admin", tags=["admin-containers"], dependencies=[Depends(require_admin)])
_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.*?-]{0,63}$")


@router.get("/containers")
async def overview(session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    docker = get_docker()
    containers: list[dict[str, Any]] = []
    error = None
    if docker.enabled:
        try:
            containers = await docker.list_containers()
        except DockerError as exc:
            error = str(exc)
    users = (await session.execute(select(User).order_by(User.created_at))).scalars().all()
    grants = (await session.execute(select(ContainerGrant).order_by(ContainerGrant.container))).scalars().all()
    by_user: dict[uuid.UUID, list[dict[str, str]]] = {}
    for g in grants:
        by_user.setdefault(g.user_id, []).append({"container": g.container, "level": g.level})
    return {
        "enabled": docker.enabled,
        "error": error,
        "containers": containers,
        "users": [
            {"id": str(u.id), "email": u.email, "name": u.name, "role": u.role, "is_active": u.is_active, "grants": by_user.get(u.id, [])}
            for u in users
        ],
    }


class GrantIn(BaseModel):
    container: str = Field(min_length=1, max_length=64)
    level: Literal["logs", "actions"]


class GrantsIn(BaseModel):
    grants: list[GrantIn] = Field(max_length=200)


@router.put("/users/{user_id}/container-grants")
async def set_grants(
    user_id: uuid.UUID, body: GrantsIn, admin: User = Depends(require_admin), session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    """Replace the user's grants with exactly this list (the highest level wins when a container is listed twice)."""
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    merged: dict[str, str] = {}
    for g in body.grants:
        name = g.container.strip()
        if not _PATTERN.match(name):
            raise HTTPException(422, f"Invalid container name or pattern: {name!r} (letters, digits, _ . - and * ? wildcards)")
        if merged.get(name) != "actions":
            merged[name] = g.level
    await session.execute(delete(ContainerGrant).where(ContainerGrant.user_id == user_id))
    for name, level in merged.items():
        session.add(ContainerGrant(user_id=user_id, container=name, level=level, created_by=admin.id))
    await session.commit()
    return {"user_id": str(user_id), "grants": [{"container": n, "level": l} for n, l in merged.items()]}


@router.get("/container-audit")
async def audit(page: int = 1, page_size: int = 25, session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    page, page_size = max(page, 1), min(max(page_size, 1), 100)
    total = (await session.execute(select(func.count(ContainerAudit.id)))).scalar_one()
    rows = (
        await session.execute(select(ContainerAudit).order_by(ContainerAudit.created_at.desc()).limit(page_size).offset((page - 1) * page_size))
    ).scalars().all()
    return {
        "total": total, "page": page, "page_size": page_size,
        "items": [
            {"id": str(r.id), "user": {"email": r.user.email, "name": r.user.name}, "container": r.container, "action": r.action,
             "result": r.result, "created_at": r.created_at}
            for r in rows
        ],
    }
