"""Admin: who may see / read logs / act on which container, plus the audit trail."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import ContainerAudit, User
from app.security import require_permission
from app.services.docker_inspector import DockerError, get_docker

router = APIRouter(prefix="/admin", tags=["admin-containers"], dependencies=[Depends(require_permission("containers.manage_access"))])


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
    return {
        "enabled": docker.enabled,
        "error": error,
        "containers": containers,
        "users": [
            {"id": str(u.id), "email": u.email, "name": u.name, "roles": [r.name for r in u.roles], "is_active": u.is_active,
             "full_access": "actions" if u.has_permission("containers.actions_all") else "logs" if u.has_permission("containers.logs_all") else None}
            for u in users
        ],
    }


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
