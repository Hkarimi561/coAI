"""Per-user container permissions.

The global DOCKER_ALLOWED_CONTAINERS list is the outer boundary nobody can exceed. Inside it:
  * admins can read logs and run actions on every allow-listed container,
  * everyone else only gets what an admin granted (exact name or glob): "logs" or "actions" (= logs + start/stop/restart).
No grant means the user cannot see the container at all - neither in the Containers page nor through the assistant.
"""

import fnmatch
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ContainerGrant, User

LEVEL_RANK = {"none": 0, "logs": 1, "actions": 2}


async def access_map(session: AsyncSession, user: User, names: list[str]) -> dict[str, str]:
    """{container: level} for the containers in `names` that `user` may access (level omitted when none)."""
    if user.role == "admin":
        return {n: "actions" for n in names}
    return await access_map_for_user_id(session, user.id, names)


async def access_map_for_user_id(session: AsyncSession, user_id: uuid.UUID, names: list[str]) -> dict[str, str]:
    grants = (await session.execute(select(ContainerGrant).where(ContainerGrant.user_id == user_id))).scalars().all()
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
