"""Knowledge-gap report: what users asked that the assistant could not answer well (per period).

A turn counts as a gap when
  * no_source    - nothing in docs / solutions / web / tools supported the answer (model knowledge only),
  * web_fallback - internal docs did not cover it and a live web search was needed,
  * rejected     - the user said the proposed fix did not work.
Similar questions are clustered by embedding similarity so recurring topics rise to the top.
"""

import logging
import re
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Feedback, TurnEvent
from app.services.container import get_embedder

log = logging.getLogger(__name__)

KINDS = ("no_source", "web_fallback", "rejected")
WEIGHT = {"no_source": 1, "web_fallback": 1, "rejected": 2}
MAX_EVENTS = 400
CLUSTER_SIM = 0.90  # e5 scores are compressed (unrelated ~0.78), so near-duplicates need a high threshold
_TRIVIAL = re.compile(r"^[\W\d_]*$")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())[:200]


def _is_trivial(q: str) -> bool:
    q = q.strip()
    return len(q) < 8 or bool(_TRIVIAL.match(q))  # greetings, "ok", "?" ...


def _cos(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))  # embeddings are L2-normalised


async def _cluster(rows: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Greedy embedding clustering; falls back to exact/normalised-text grouping if embeddings fail."""
    try:
        vecs: list[list[float]] = []
        texts = [r["query"][:300] for r in rows]
        for i in range(0, len(texts), 32):
            vecs.extend(await get_embedder().embed(texts[i:i + 32], "query"))
        centroids: list[list[float]] = []
        groups: list[list[dict[str, Any]]] = []
        for r, v in zip(rows, vecs, strict=True):
            best, best_s = -1, 0.0
            for i, c in enumerate(centroids):
                s = _cos(v, c)
                if s > best_s:
                    best, best_s = i, s
            if best >= 0 and best_s >= CLUSTER_SIM:
                groups[best].append(r)
            else:
                centroids.append(v)
                groups.append([r])
        return groups
    except Exception:
        log.exception("gap clustering by embeddings failed; grouping by text")
        by_key: dict[str, list[dict[str, Any]]] = {}
        for r in rows:
            by_key.setdefault(r["signature"] or _norm(r["query"]), []).append(r)
        return list(by_key.values())


async def _window(session: AsyncSession, start: datetime, end: datetime) -> tuple[int, list[dict[str, Any]]]:
    total = (await session.execute(select(func.count()).select_from(TurnEvent).where(TurnEvent.created_at >= start, TurnEvent.created_at < end))).scalar_one()
    events = (
        await session.execute(
            select(TurnEvent).where(TurnEvent.created_at >= start, TurnEvent.created_at < end).order_by(TurnEvent.created_at.desc()).limit(MAX_EVENTS * 3)
        )
    ).scalars().all()
    rejected_ids = set(
        (await session.execute(select(Feedback.message_id).where(Feedback.outcome == "rejected", Feedback.created_at >= start, Feedback.created_at < end))).scalars()
    )
    rows: list[dict[str, Any]] = []
    for e in events:
        if _is_trivial(e.query_text or ""):
            continue
        kinds = []
        if e.primary_source == "none" and not (e.sources or []):
            kinds.append("no_source")
        if e.web_event == "fresh":
            kinds.append("web_fallback")
        if e.message_id in rejected_ids:
            kinds.append("rejected")
        if kinds:
            rows.append({"query": e.query_text, "kinds": kinds, "conversation_id": str(e.conversation_id), "at": e.created_at, "signature": e.error_signature})
    return total, rows[:MAX_EVENTS]


async def compute(session: AsyncSession, days: int = 7) -> dict[str, Any]:
    now = datetime.now(UTC)
    start, prev_start = now - timedelta(days=days), now - timedelta(days=days * 2)
    total, rows = await _window(session, start, now + timedelta(minutes=1))
    prev_total, prev_rows = await _window(session, prev_start, start)

    clusters = []
    for group in await _cluster(rows) if rows else []:
        kinds = {k: 0 for k in KINDS}
        for r in group:
            for k in r["kinds"]:
                kinds[k] += 1
        group.sort(key=lambda r: r["at"], reverse=True)
        clusters.append({
            "title": group[0]["query"].strip().splitlines()[0][:140],
            "count": len(group),
            "score": sum(WEIGHT[k] * n for k, n in kinds.items()),
            "kinds": kinds,
            "last_seen": group[0]["at"].isoformat(),
            "examples": [{"query": r["query"].strip()[:300], "conversation_id": r["conversation_id"], "at": r["at"].isoformat()} for r in group[:4]],
        })
    clusters.sort(key=lambda c: (-c["score"], -c["count"]))
    return {
        "days": days,
        "from": start.isoformat(),
        "to": now.isoformat(),
        "turns": total,
        "gap_turns": len(rows),
        "gap_rate": round(len(rows) / total, 3) if total else 0.0,
        "previous": {"turns": prev_total, "gap_turns": len(prev_rows), "gap_rate": round(len(prev_rows) / prev_total, 3) if prev_total else 0.0},
        "kinds": {k: sum(1 for r in rows if k in r["kinds"]) for k in KINDS},
        "clusters": clusters[:50],
    }


_KIND_FA = {"no_source": "بدون منبع (فقط دانش مدل)", "web_fallback": "نیاز به جستجوی وب", "rejected": "راه‌حل رد شد"}


def to_markdown(report: dict[str, Any]) -> str:
    """Report as a Markdown document an admin can download and share."""
    p = report["previous"]
    lines = [
        f"# گزارش شکاف‌های دانش — {report['days']} روز اخیر",
        "",
        f"- بازه: {report['from'][:10]} تا {report['to'][:10]}",
        f"- پاسخ‌های دستیار: {report['turns']} — پاسخ‌های ضعیف: {report['gap_turns']} ({round(report['gap_rate'] * 100)}٪)",
        f"- دوره‌ی قبل: {p['gap_turns']} از {p['turns']} ({round(p['gap_rate'] * 100)}٪)",
        "- "
        + "، ".join(f"{_KIND_FA[k]}: {n}" for k, n in report["kinds"].items()),
        "",
        "## موضوع‌هایی که باید مستند یا مهارت برایشان نوشته شود",
        "",
    ]
    if not report["clusters"]:
        lines.append("موردی ثبت نشده است. 🎉")
    for i, c in enumerate(report["clusters"], 1):
        kinds = "، ".join(f"{_KIND_FA[k]} ×{n}" for k, n in c["kinds"].items() if n)
        lines += [f"### {i}. {c['title']}", f"- تعداد: {c['count']} — {kinds}", f"- آخرین بار: {c['last_seen'][:16].replace('T', ' ')}", "- نمونه سؤال‌ها:"]
        lines += [f"  - {e['query'][:200].replace(chr(10), ' ')}" for e in c["examples"]]
        lines.append("")
    return "\n".join(lines)
