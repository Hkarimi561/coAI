"""Containers page API: what the current user may see, read and (if granted) start / stop / restart."""

import re
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal, get_session
from app.models import ContainerAudit, User
from app.redaction import redact
from app.redis_client import rate_limit
from app.security import get_current_user
from app.services import container_access
from app.services.docker_inspector import DockerError, get_docker

router = APIRouter(prefix="/containers", tags=["containers"])
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


async def _level(session: AsyncSession, user: User, name: str) -> str | None:
    if not _NAME.match(name):
        raise HTTPException(404, "Container not found")
    return (await container_access.access_map(session, user, [name])).get(name)


async def _audit(user: User, name: str, action: str, result: str) -> None:
    async with SessionLocal() as s:  # own session: denied attempts must be recorded even though the request fails
        s.add(ContainerAudit(user_id=user.id, container=name, action=action, result=result[:300]))
        await s.commit()


@router.get("")
async def my_containers(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    docker = get_docker()
    if not docker.enabled:
        return {"enabled": False, "items": [], "actions_hint": "Docker inspection is not enabled (DOCKER_ALLOWED_CONTAINERS is empty)."}
    try:
        containers = await docker.list_containers()
    except DockerError as exc:
        raise HTTPException(502, str(exc)) from exc
    access = await container_access.access_map(session, user, [c["name"] for c in containers])
    return {"enabled": True, "items": [{**c, "level": access[c["name"]]} for c in containers if c["name"] in access]}


@router.get("/{name}/logs")
async def container_logs(
    name: str, tail: int = Query(default=200, ge=10, le=2000), user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    if not container_access.allows(await _level(session, user, name), "logs"):
        raise HTTPException(404, "Container not found")  # do not reveal containers the user cannot see
    try:
        return {"name": name, "tail": tail, "logs": redact(await get_docker().read_logs(name, tail))}
    except DockerError as exc:
        raise HTTPException(502, str(exc)) from exc


class ActionIn(BaseModel):
    action: Literal["start", "stop", "restart"]


@router.post("/{name}/actions")
async def container_action(
    name: str, body: ActionIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    await rate_limit(f"cact:{user.id}", 10, 60)
    level = await _level(session, user, name)
    if not container_access.allows(level, "actions"):
        await _audit(user, name, body.action, "denied")
        raise HTTPException(403 if level else 404, "You do not have permission to run actions on this container")
    try:
        await get_docker().action(name, body.action)
    except DockerError as exc:
        await _audit(user, name, body.action, f"error: {exc}")
        raise HTTPException(502, str(exc)) from exc
    await _audit(user, name, body.action, "ok")
    return {"name": name, "action": body.action, "ok": True}
