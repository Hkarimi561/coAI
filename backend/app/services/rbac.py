"""Roles and permissions: built-in roles, escalation and lock-out guards.

Rules enforced here (the API layer calls them):
  * the `admin` role always holds every permission in the catalog (re-synced on each start),
  * nobody can hand out a permission they do not hold themselves,
  * nobody can change a user who holds permissions the actor lacks (no resetting an admin's password with `users.manage` alone),
  * at least one active user must always hold both `users.manage` and `roles.manage`.
"""

import uuid
from collections.abc import Iterable

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Role, RolePermission, User
from app.permissions import ADMIN_ROLE, ALL_KEYS, USER_ROLE

_SYSTEM_ROLES = {
    ADMIN_ROLE: "Full access to everything",
    USER_ROLE: "Default role: can chat with the assistant",
}


async def ensure_system_roles(session: AsyncSession) -> dict[str, Role]:
    """Creates the built-in roles if missing, gives `admin` every known permission and drops permission keys that no longer exist."""
    await session.execute(delete(RolePermission).where(RolePermission.permission.not_in(ALL_KEYS)))
    rows = (await session.execute(select(Role).where(Role.name.in_(_SYSTEM_ROLES)))).scalars().all()
    by_name = {r.name: r for r in rows}
    for name, description in _SYSTEM_ROLES.items():
        if name not in by_name:
            by_name[name] = Role(name=name, description=description, is_system=True)
            session.add(by_name[name])
    admin = by_name[ADMIN_ROLE]
    for key in sorted(ALL_KEYS - {g.permission for g in admin.grants}):
        admin.grants.append(RolePermission(permission=key))
    await session.commit()
    return by_name


async def roles_by_ids(session: AsyncSession, role_ids: Iterable[uuid.UUID]) -> list[Role]:
    ids = set(role_ids)
    if not ids:
        return []
    roles = list((await session.execute(select(Role).where(Role.id.in_(ids)))).scalars().all())
    if len(roles) != len(ids):
        raise HTTPException(422, "One or more roles do not exist")
    return roles


async def default_roles(session: AsyncSession) -> list[Role]:
    return [(await ensure_system_roles(session))[USER_ROLE]]


def require_can_grant(actor: User, permissions: Iterable[str]) -> None:
    """Raises 403 unless `actor` already holds every permission in `permissions`."""
    missing = sorted(set(permissions) - set(actor.permissions))
    if missing:
        raise HTTPException(403, f"You cannot grant permissions you do not have: {', '.join(missing)}")


def require_can_manage(actor: User, target: User) -> None:
    """Raises 403 when `target` holds permissions the actor lacks."""
    if target.id != actor.id and set(target.permissions) - set(actor.permissions):
        raise HTTPException(403, "You cannot modify a user who has more permissions than you")


async def ensure_managers_remain(session: AsyncSession) -> None:
    """Call after changing roles / activation, before commit: rolls back when nobody could manage users and roles any more."""
    users = (await session.execute(select(User).where(User.is_active.is_(True)))).scalars().all()
    if not any(u.has_permission("users.manage") and u.has_permission("roles.manage") for u in users):
        await session.rollback()
        raise HTTPException(409, "At least one active user must keep both the users.manage and roles.manage permissions")
