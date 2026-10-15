"""Admin API: users (with their roles) and roles (with their permissions)."""

import uuid
from typing import Any

import re
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Role, RoleContainerGrant, RolePermission, User, user_roles
from app.permissions import ADMIN_ROLE, ALL_KEYS, CATALOG
from app.schemas import UserCreate, UserOut, UserUpdate
from app.security import hash_password, require_any_of, require_permission
from app.services import rbac

router = APIRouter(prefix="/admin", tags=["admin-rbac"])

_either = Depends(require_any_of("users.manage", "roles.manage"))


# ------------------------------------------------------------------ permission catalog + roles
_CONTAINER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.*?-]{0,63}$")


class ContainerGrantIn(BaseModel):
    container: str = Field(min_length=1, max_length=64)
    level: Literal["logs", "actions"]


class RoleIn(BaseModel):
    name: str = Field(min_length=2, max_length=48)
    description: str = Field(default="", max_length=200)
    permissions: list[str] = Field(default_factory=list, max_length=100)
    container_grants: list[ContainerGrantIn] = Field(default_factory=list, max_length=200)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=48)
    description: str | None = Field(default=None, max_length=200)
    permissions: list[str] | None = Field(default=None, max_length=100)
    container_grants: list[ContainerGrantIn] | None = Field(default=None, max_length=200)  # replaces all when given


def _merge_container_grants(items: list[ContainerGrantIn]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for g in items:
        name = g.container.strip()
        if not _CONTAINER.match(name):
            raise HTTPException(422, f"Invalid container name or pattern: {name!r} (letters, digits, _ . - and * ? wildcards)")
        if merged.get(name) != "actions":
            merged[name] = g.level
    return merged


def _role_out(r: Role, user_count: int) -> dict[str, Any]:
    return {"id": str(r.id), "name": r.name, "description": r.description, "is_system": r.is_system,
            "locked": r.name == ADMIN_ROLE, "permissions": r.permissions, "user_count": user_count,
            "container_grants": [{"container": g.container, "level": g.level} for g in r.container_grants]}


def _valid_permissions(keys: list[str]) -> set[str]:
    unknown = sorted(set(keys) - ALL_KEYS)
    if unknown:
        raise HTTPException(422, f"Unknown permission(s): {', '.join(unknown)}")
    return set(keys)


async def _role(session: AsyncSession, role_id: uuid.UUID) -> Role:
    role = await session.get(Role, role_id)
    if role is None:
        raise HTTPException(404, "Role not found")
    return role


async def _counts(session: AsyncSession) -> dict[uuid.UUID, int]:
    rows = (await session.execute(select(user_roles.c.role_id, func.count()).group_by(user_roles.c.role_id))).all()
    return {rid: n for rid, n in rows}


@router.get("/permissions", dependencies=[_either])
async def list_permissions() -> list[dict[str, str]]:
    return [{"key": p.key, "group": p.group, "label": p.label} for p in CATALOG]


@router.get("/roles", dependencies=[_either])
async def list_roles(session: AsyncSession = Depends(get_session)) -> list[dict[str, Any]]:
    roles = (await session.execute(select(Role).order_by(Role.is_system.desc(), Role.name))).scalars().all()
    counts = await _counts(session)
    return [_role_out(r, counts.get(r.id, 0)) for r in roles]


@router.post("/roles", status_code=201)
async def create_role(
    body: RoleIn, actor: User = Depends(require_permission("roles.manage")), session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    keys = _valid_permissions(body.permissions)
    rbac.require_can_grant(actor, keys)
    containers = _merge_container_grants(body.container_grants)
    if containers:
        rbac.require_can_grant(actor, {"containers.manage_access"})
    role = Role(name=body.name.strip(), description=body.description.strip(), is_system=False,
                grants=[RolePermission(permission=k) for k in sorted(keys)],
                container_grants=[RoleContainerGrant(container=c, level=lv) for c, lv in containers.items()])
    session.add(role)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(409, "A role with this name already exists") from None
    return _role_out(role, 0)


@router.patch("/roles/{role_id}")
async def update_role(
    role_id: uuid.UUID, body: RoleUpdate, actor: User = Depends(require_permission("roles.manage")), session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    role = await _role(session, role_id)
    if body.name is not None and body.name.strip() != role.name:
        if role.is_system:
            raise HTTPException(409, "Built-in roles cannot be renamed")
        role.name = body.name.strip()
    if body.description is not None:
        role.description = body.description.strip()
    if body.permissions is not None:
        if role.name == ADMIN_ROLE:
            raise HTTPException(409, "The admin role always has every permission and cannot be changed")
        new = _valid_permissions(body.permissions)
        old = set(role.permissions)
        rbac.require_can_grant(actor, new - old)
        for g in [g for g in role.grants if g.permission not in new]:
            role.grants.remove(g)
        role.grants.extend(RolePermission(permission=k) for k in sorted(new - old))
    if body.container_grants is not None:
        if role.name == ADMIN_ROLE:
            raise HTTPException(409, "The admin role already has access to every container")
        containers = _merge_container_grants(body.container_grants)
        if containers != {g.container: g.level for g in role.container_grants}:
            rbac.require_can_grant(actor, {"containers.manage_access"})
            for g in list(role.container_grants):
                if g.container not in containers:
                    role.container_grants.remove(g)
                else:
                    g.level = containers[g.container]  # update in place (unique per role + container)
            have = {g.container for g in role.container_grants}
            role.container_grants.extend(RoleContainerGrant(container=c, level=lv) for c, lv in containers.items() if c not in have)
    try:
        await rbac.ensure_managers_remain(session)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(409, "A role with this name already exists") from None
    return _role_out(role, (await _counts(session)).get(role.id, 0))


@router.delete("/roles/{role_id}", status_code=204, dependencies=[Depends(require_permission("roles.manage"))])
async def delete_role(role_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> None:
    role = await _role(session, role_id)
    if role.is_system:
        raise HTTPException(409, "Built-in roles cannot be deleted")
    n = (await _counts(session)).get(role.id, 0)
    if n:
        raise HTTPException(409, f"{n} user(s) still have this role; remove it from them first")
    await session.delete(role)
    await session.commit()


# ------------------------------------------------------------------ users
@router.get("/users", response_model=list[UserOut], dependencies=[Depends(require_permission("users.manage"))])
async def list_users(session: AsyncSession = Depends(get_session)) -> list[User]:
    return list((await session.execute(select(User).order_by(User.created_at))).scalars().all())


@router.post("/users", response_model=UserOut, status_code=201)
async def create_user(
    body: UserCreate, actor: User = Depends(require_permission("users.manage")), session: AsyncSession = Depends(get_session)
) -> User:
    roles = await rbac.roles_by_ids(session, body.role_ids) if body.role_ids is not None else await rbac.default_roles(session)
    rbac.require_can_grant(actor, {p for r in roles for p in r.permissions})
    user = User(email=body.email.strip().lower(), name=body.name.strip(), password_hash=hash_password(body.password), roles=roles)
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(409, "A user with this e-mail already exists") from None
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID, body: UserUpdate, actor: User = Depends(require_permission("users.manage")), session: AsyncSession = Depends(get_session)
) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    if user.id == actor.id and (body.is_active is False or body.role_ids is not None):
        raise HTTPException(409, "You cannot disable your own account or change your own roles")
    rbac.require_can_manage(actor, user)
    if body.role_ids is not None:
        roles = await rbac.roles_by_ids(session, body.role_ids)
        current = {r.id for r in user.roles}
        rbac.require_can_grant(actor, {p for r in roles if r.id not in current for p in r.permissions})
        user.roles = roles
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.password:
        user.password_hash = hash_password(body.password)
    await rbac.ensure_managers_remain(session)
    await session.commit()
    return user
