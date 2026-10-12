"""Skills: admin-authored Markdown playbooks, matched to the user's question by embedding similarity of their description."""

import logging
import uuid

from qdrant_client import models
from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.models import Skill
from app.services.container import get_embedder, get_vectorstore

log = logging.getLogger(__name__)


async def index_skill(skill: Skill) -> None:
    """(Re)index one skill; disabled skills are removed from the index."""
    store = get_vectorstore()
    await store.delete_where(kind="skill", ref=f"skill:{skill.id}")
    if not skill.enabled:
        return
    [vec] = await get_embedder().embed([f"{skill.name}\n{skill.description}"], "passage")
    await store.upsert([models.PointStruct(
        id=str(skill.id), vector=vec,
        payload={"kind": "skill", "ref": f"skill:{skill.id}", "skill_id": str(skill.id), "title": skill.name, "text": skill.description},
    )])


async def remove_skill(skill_id: uuid.UUID) -> None:
    try:
        await get_vectorstore().delete_where(kind="skill", ref=f"skill:{skill_id}")
    except Exception:
        log.exception("Could not remove skill vector %s", skill_id)


async def reindex_all() -> None:
    async with SessionLocal() as session:
        skills = (await session.execute(select(Skill))).scalars().all()
    for s in skills:
        try:
            await index_skill(s)
        except Exception:
            log.exception("Could not index skill %s", s.name)


async def select_for(vec: list[float], limit: int = 2) -> list[Skill]:
    """Skills whose description matches the question (best first)."""
    hits = await get_vectorstore().search(vec, ["skill"], limit)
    best = max((h.score for h in hits), default=0.0)
    # e5 scores are compressed (unrelated pairs ~0.78-0.82): require a high score, and a 2nd skill only if it is nearly as good as the best
    wanted = [h.payload.get("skill_id") for h in hits if h.score >= get_settings().skill_min_score and h.score >= best - 0.03]
    if not wanted:
        return []
    async with SessionLocal() as session:
        rows = (await session.execute(select(Skill).where(Skill.id.in_([uuid.UUID(w) for w in wanted]), Skill.enabled.is_(True)))).scalars().all()
    by_id = {str(r.id): r for r in rows}
    return [by_id[w] for w in wanted if w in by_id]
