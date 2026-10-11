"""Persistence around the workflow: turns, feedback loop, candidate solutions."""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from qdrant_client import models
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal
from app.models import Conversation, Feedback, Message, Solution, ToolCall, TurnEvent, User
from app.redaction import redact, redact_obj
from app.schemas import MessageOut
from app.services.container import get_embedder, get_vectorstore
from app.services.workflow import Emit, TroubleshootingWorkflow, TurnState
from app.textnorm import truncate_middle

log = logging.getLogger(__name__)
_workflow = TroubleshootingWorkflow()

ASK_FOR_ERROR = (
    "متوجه شدم، این راه‌حل جواب نداد. لطفاً **خطای جدید یا خروجی دستور** را همین‌جا بچسبانید "
    "(در صورت امکان خروجی کامل `docker logs --tail 100 <container>` یا پیام خطای دقیق). "
    "با استفاده از اطلاعات جدید و بدون تکرار پیشنهادهای قبلی دوباره جستجو می‌کنم."
)
CONFIRM_ACK = "عالی! راه‌حل به‌عنوان «راه‌حل تأییدشده» ثبت شد و برای بازبینی ادمین در صف قرار گرفت. ممنون از بازخورد شما."


def _history_for_llm(rows: list[Message]) -> list[dict[str, str]]:
    return [{"role": m.role, "content": truncate_middle(m.content, 1800)} for m in rows if m.meta.get("kind") != "request_error"]


async def run_turn(*, conversation_id: uuid.UUID, content: str, emit: Emit) -> None:
    """Runs one user turn end-to-end. Never raises; failures are emitted as `error` events."""
    try:
        redacted = redact(content).strip()
        async with SessionLocal() as session:
            convo = await session.get(Conversation, conversation_id)
            assert convo is not None
            prev = (
                await session.execute(
                    select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.desc()).limit(8)
                )
            ).scalars().all()
            history = _history_for_llm(list(reversed(prev)))

            state: dict[str, Any] = dict(convo.state or {})
            if state.get("phase", "idle") == "idle" or not state.get("original_problem"):
                state = {"phase": "idle", "attempts": 0, "rejected_refs": [], "failed_summaries": [], "original_problem": redacted[:1500]}
            if not convo.title:
                convo.title = redacted.strip().splitlines()[0][:80] if redacted.strip() else "گفتگوی جدید"
            user_msg = Message(conversation_id=conversation_id, role="user", content=redacted)
            session.add(user_msg)
            convo.state = state
            convo.updated_at = datetime.now(UTC)
            await session.commit()
            await emit("user_message", MessageOut.of(user_msg).model_dump(mode="json"))

        st = TurnState(conversation_id=str(conversation_id), message=redacted, history=history, convo_state=state)
        await _workflow.run(st, emit)

        sig = st.signature
        meta = {
            "awaiting_feedback": bool(st.items) and not st.llm_error,
            "primary_source": st.primary_source,
            "web_event": st.web_event,
            "signature_key": sig.key if sig else None,
            "refs": st.refs,
            "notes": st.notes,
            **({"llm_error": redact(st.llm_error)} if st.llm_error else {}),
        }
        async with SessionLocal() as session:
            msg = Message(conversation_id=conversation_id, role="assistant", content=st.answer, citations=redact_obj(st.citations), meta=meta)
            session.add(msg)
            await session.flush()
            for tc in st.tool_calls:
                session.add(ToolCall(conversation_id=conversation_id, message_id=msg.id, tool=tc["tool"], input=redact_obj(tc["input"]),
                                     output=redact_obj(tc["output"]), status=tc["status"], duration_ms=tc["duration_ms"]))
            session.add(
                TurnEvent(
                    conversation_id=conversation_id, message_id=msg.id, query_text=redacted[:500],
                    error_signature=sig.key if sig and sig.is_error else None,
                    signature_text=sig.text[:500] if sig and sig.is_error else None,
                    primary_source=st.primary_source, sources=st.sources, web_event=st.web_event,
                )
            )
            convo = await session.get(Conversation, conversation_id)
            assert convo is not None
            new_state = dict(convo.state or {})
            if meta["awaiting_feedback"]:
                new_state["phase"] = "awaiting_feedback"
            convo.state = new_state
            convo.updated_at = datetime.now(UTC)
            await session.commit()
            await emit("done", MessageOut.of(msg).model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        log.exception("Turn failed")
        await emit("error", {"message": redact(f"{type(exc).__name__}: {exc}")[:300]})


async def submit_feedback(
    session: AsyncSession, user: User, convo: Conversation, message_id: uuid.UUID, outcome: str, note: str
) -> Message | None:
    msg = await session.get(Message, message_id)
    if msg is None or msg.conversation_id != convo.id or msg.role != "assistant":
        raise HTTPException(404, "Message not found")
    if not msg.meta.get("awaiting_feedback"):
        raise HTTPException(409, "Feedback was already given or is not applicable for this message")

    note = redact(note).strip()
    state = dict(convo.state or {})
    msg.meta = {**msg.meta, "awaiting_feedback": False, "feedback": outcome}
    fb = Feedback(conversation_id=convo.id, message_id=msg.id, user_id=user.id, outcome=outcome, note=note)
    session.add(fb)

    if outcome == "confirmed":
        problem = state.get("original_problem") or ""
        last_user = (
            await session.execute(
                select(Message).where(Message.conversation_id == convo.id, Message.role == "user").order_by(Message.created_at.desc()).limit(1)
            )
        ).scalar_one_or_none()
        if last_user and last_user.content not in problem:
            problem = f"{problem}\n\nFinal error/context:\n{last_user.content}"[:3000]
        sol = Solution(
            conversation_id=convo.id, message_id=msg.id, title=(problem.strip().splitlines() or ["Solution"])[0][:200] or "Solution",
            problem=problem, error_signature=msg.meta.get("signature_key"), content=msg.content, citations=msg.citations or [],
        )
        session.add(sol)
        await session.flush()
        fb.solution_id = sol.id
        convo.status = "pending_review"
        convo.state = {"phase": "idle", "attempts": 0, "rejected_refs": [], "failed_summaries": [], "original_problem": None}
        ack = Message(conversation_id=convo.id, role="assistant", content=CONFIRM_ACK, meta={"kind": "ack"})
        session.add(ack)
        await session.commit()
        await index_solution(sol)
        return ack

    # rejected: remember what failed, then ask for the new error output
    failed = list(state.get("failed_summaries", []))
    failed.append(truncate_middle(msg.content, 700))
    state.update(
        phase="awaiting_error",
        attempts=int(state.get("attempts", 0)) + 1,
        rejected_refs=sorted(set(state.get("rejected_refs", [])) | set(msg.meta.get("refs", []))),
        failed_summaries=failed[-3:],
    )
    convo.state = state
    convo.status = "unresolved"
    ask = Message(conversation_id=convo.id, role="assistant", content=ASK_FOR_ERROR, meta={"kind": "request_error"})
    session.add(ask)
    await session.commit()
    return ask


async def index_solution(sol: Solution) -> None:
    try:
        [vec] = await get_embedder().embed([f"{sol.title}\n{sol.problem[:1500]}"], "passage")
        await get_vectorstore().upsert(
            [
                models.PointStruct(
                    id=str(sol.id), vector=vec,
                    payload={"kind": "solution", "ref": f"sol:{sol.id}", "solution_id": str(sol.id), "title": sol.title,
                             "text": sol.content, "status": sol.status},
                )
            ]
        )
    except Exception:
        log.exception("Could not index solution %s; it is stored in PostgreSQL but not retrievable semantically", sol.id)


async def remove_solution_vector(solution_id: uuid.UUID) -> None:
    try:
        await get_vectorstore().delete_where(kind="solution", ref=f"sol:{solution_id}")
    except Exception:
        log.exception("Could not remove solution vector %s", solution_id)
