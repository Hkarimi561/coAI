"""Admin analytics computed from PostgreSQL (turn_events, conversations, feedback, web_cache)."""

from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation, Feedback, TurnEvent, WebCacheEntry

SOURCE_KEYS = ["local_docs", "solutions", "web_cache", "web_fresh", "docker", "ci"]


async def compute(session: AsyncSession, days: int = 30) -> dict[str, Any]:
    since = datetime.now(UTC) - timedelta(days=days)

    total = (await session.execute(select(func.count(Conversation.id)))).scalar_one()
    status_rows = (await session.execute(select(Conversation.status, func.count()).group_by(Conversation.status))).all()
    by_status = {s: n for s, n in status_rows}
    answered = (await session.execute(select(func.count(func.distinct(TurnEvent.conversation_id))))).scalar_one()
    solved = by_status.get("resolved", 0) + by_status.get("pending_review", 0)

    # Source distribution: each turn counts every distinct source kind its answer relied on.
    events = (await session.execute(select(TurnEvent.sources, TurnEvent.web_event, TurnEvent.created_at).where(TurnEvent.created_at >= since))).all()
    sources: Counter[str] = Counter()
    web_events: Counter[str] = Counter()
    for srcs, web_event, _ in events:
        sources.update(srcs or [])
        web_events[web_event] += 1
    avoided = web_events["cache_hit"] + web_events["coalesced"]
    fresh = web_events["fresh"]

    # Conversations per day
    day = func.date_trunc("day", Conversation.created_at)
    per_day_rows = (
        await session.execute(select(day, func.count()).where(Conversation.created_at >= since).group_by(day).order_by(day))
    ).all()
    per_day_map = {d.date().isoformat(): n for d, n in per_day_rows}
    series = []
    for i in range(days - 1, -1, -1):
        d = (datetime.now(UTC) - timedelta(days=i)).date().isoformat()
        series.append({"date": d, "conversations": per_day_map.get(d, 0)})

    # Top recurring error signatures
    sig_rows = (
        await session.execute(
            select(
                TurnEvent.error_signature,
                func.count().label("n"),
                func.count(func.distinct(TurnEvent.conversation_id)).label("convos"),
                func.max(TurnEvent.created_at).label("last_seen"),
                func.min(TurnEvent.signature_text).label("text"),
            )
            .where(TurnEvent.error_signature.is_not(None), TurnEvent.created_at >= since)
            .group_by(TurnEvent.error_signature)
            .order_by(func.count().desc())
            .limit(10)
        )
    ).all()

    fb_rows = (await session.execute(select(Feedback.outcome, func.count()).group_by(Feedback.outcome))).all()
    feedback = {o: n for o, n in fb_rows}
    cache_total = (await session.execute(select(func.count(WebCacheEntry.id)).where(WebCacheEntry.invalidated_at.is_(None)))).scalar_one()
    cache_hits_total = (await session.execute(select(func.coalesce(func.sum(WebCacheEntry.hit_count), 0)))).scalar_one()

    return {
        "days": days,
        "totals": {
            "conversations": total,
            "answered_conversations": answered,
            "resolved": solved,
            "resolution_rate": round(solved / total, 4) if total else 0.0,
            "turns": len(events),
        },
        "by_status": {k: by_status.get(k, 0) for k in ("unresolved", "pending_review", "resolved")},
        "feedback": {"confirmed": feedback.get("confirmed", 0), "rejected": feedback.get("rejected", 0)},
        "sources": [{"source": k, "count": sources.get(k, 0)} for k in SOURCE_KEYS],
        "web": {
            "searches_performed": fresh,
            "searches_avoided": avoided,
            "cache_hit_rate": round(avoided / (avoided + fresh), 4) if (avoided + fresh) else 0.0,
            "failed": web_events["failed"],
            "cache_entries": cache_total,
            "cache_hits_total": int(cache_hits_total),
        },
        "conversations_per_day": series,
        "top_signatures": [
            {"signature": key, "text": text, "occurrences": n, "conversations": convos, "last_seen": last.isoformat()}
            for key, n, convos, last, text in sig_rows
        ],
    }
