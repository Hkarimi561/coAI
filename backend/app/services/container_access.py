"""Per-user container permissions.

The global DOCKER_ALLOWED_CONTAINERS list is the outer boundary nobody can exceed. Inside it:
  * the role permissions containers.logs_all / containers.actions_all open every allow-listed container,
  * on top of that a user gets what their roles grant per container (exact name or glob): "logs" or "actions"
    (= logs + start/stop/restart). The highest level wins. Roles are the only source: the legacy per-user grants table is ignored.
No grant means the user cannot see the container at all - neither in the Containers page nor through the assistant.
"""

import fnmatch
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RoleContainerGrant, User, user_roles

LEVEL_RANK = {"none": 0, "logs": 1, "actions": 2}


async def access_map(session: AsyncSession, user: User, names: list[str]) -> dict[str, str]:
    """{container: level} for the containers in `names` that `user` may access (level omitted when none)."""
    floor = "actions" if user.has_permission("containers.actions_all") else "logs" if user.has_permission("containers.logs_all") else "none"
    if floor == "actions":
        return {n: "actions" for n in names}
    out = await access_map_for_user_id(session, user.id, names)
    if floor == "logs":
        for n in names:
            out.setdefault(n, "logs")
    return out


async def access_map_for_user_id(session: AsyncSession, user_id: uuid.UUID, names: list[str]) -> dict[str, str]:
    grants = (await session.execute(
        select(RoleContainerGrant).join(user_roles, user_roles.c.role_id == RoleContainerGrant.role_id).where(user_roles.c.user_id == user_id)
    )).scalars().all()
    out: dict[str, str] = {}
    for name in names:
        best = "none"
        for g in grants:
            if fnmatch.fnmatch(name, g.container) and LEVEL_RANK.get(g.level, 0) > LEVEL_RANK[best]:
                best = g.level
        if best != "none":
            out[name] = best
    return out


def allows(level: str | None, needed: str) -> bool:
    return LEVEL_RANK.get(level or "none", 0) >= LEVEL_RANK[needed]
