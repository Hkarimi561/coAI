"""Persistence around the workflow: turns, feedback loop, candidate solutions."""

import logging
import re
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
from app.services import answer_cache, memory
from app.services.answer_cache import bump_kb_version
from app.services.container import get_embedder, get_llm, get_vectorstore
from app.services.lessons import TEACH_PROMPT
from app.services.llm import LLMError
from app.services.workflow import Emit, TroubleshootingWorkflow, TurnState
from app.textnorm import truncate_middle

log = logging.getLogger(__name__)
_workflow = TroubleshootingWorkflow()
_RESEARCH_RE = re.compile(
    r"(?i)(دوباره|مجدد|باز\s?هم|re-?search|again|retry).{0,25}(جستجو|بگرد|سرچ|search)"
    r"|(جستجو|بگرد|سرچ|search).{0,25}(دوباره|مجدد|again)"
)

ASK_FOR_ERROR = (
    "متوجه شدم، این راه‌حل جواب نداد. لطفاً **خطای جدید یا خروجی دستور** را همین‌جا بچسبانید "
    "(در صورت امکان خروجی کامل `docker logs --tail 100 <container>` یا پیام خطای دقیق). "
    "با استفاده از اطلاعات جدید و بدون تکرار پیشنهادهای قبلی دوباره جستجو می‌کنم."
)
CONFIRM_ACK = "عالی! راه‌حل به‌عنوان «راه‌حل تأییدشده» ثبت شد و برای بازبینی ادمین در صف قرار گرفت. ممنون از بازخورد شما."


def _history_for_llm(rows: list[Message]) -> list[dict[str, str]]:
    return [{"role": m.role, "content": truncate_middle(m.content, 1800)} for m in rows if m.meta.get("kind") != "request_error"]


async def run_turn(*, conversation_id: uuid.UUID, content: str, emit: Emit, refresh: bool = False, user_id: uuid.UUID | None = None, is_admin: bool = False) -> None:
    """Runs one user turn end-to-end. Never raises; failures are emitted as `error` events."""
    try:
        redacted = redact(content).strip()
        short_research_request = len(redacted) < 80 and bool(_RESEARCH_RE.search(redacted))
        refresh = refresh or short_research_request
        async with SessionLocal() as session:
            convo = await session.get(Conversation, conversation_id)
            assert convo is not None
            prev = (
                await session.execute(
                    select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.desc()).limit(8)
                )
            ).scalars().all()
            history = _history_for_llm(list(reversed(prev)))
            # "search again" without a question means: redo the previous user question
            effective = redacted
            if short_research_request:
                effective = next((m.content for m in prev if m.role == "user"), redacted)

            is_teach = convo.mode == "teach"
            state: dict[str, Any] = dict(convo.state or {})
            if not is_teach and (state.get("phase", "idle") == "idle" or not state.get("original_problem")):
                state = {"phase": "idle", "attempts": 0, "rejected_refs": [], "failed_summaries": [], "original_problem": effective[:1500],
                         "memory": state.get("memory")}
            if not convo.title:
                convo.title = redacted.strip().splitlines()[0][:80] if redacted.strip() else "گفتگوی جدید"
            user_msg = Message(conversation_id=conversation_id, role="user", content=redacted)
            session.add(user_msg)
            convo.state = state
            convo.updated_at = datetime.now(UTC)
            await session.commit()
            await emit("user_message", MessageOut.of(user_msg).model_dump(mode="json"))

        if is_teach:
            await _teach_turn(conversation_id, emit)
            return

        st = TurnState(conversation_id=str(conversation_id), message=effective, history=history, convo_state=state, refresh=refresh,
                       user_id=str(user_id) if user_id else None, is_admin=is_admin)
        await _workflow.run(st, emit)

        sig = st.signature
        meta = {
            "awaiting_feedback": (bool(st.items) or st.cache_hit) and not st.llm_error,
            "primary_source": st.primary_source,
            "web_event": st.web_event,
            "signature_key": sig.key if sig else None,
            "refs": st.refs,
            "notes": st.notes,
            **({"answer_cache": "hit"} if st.cache_hit else {}),
            **({"answer_cache_key": st.cache_key} if st.cache_key else {}),
            **({"refreshed": True} if st.refresh else {}),
            **({"thinking": st.thinking} if st.thinking else {}),
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
            new_state["memory"] = memory.add_turn(
                new_state.get("memory"), problem=new_state.get("original_problem") or effective, user=effective,
                assistant=st.answer, source="answer_cache" if st.cache_hit else st.primary_source, awaiting=meta["awaiting_feedback"],
            )
            convo.state = new_state
            convo.updated_at = datetime.now(UTC)
            await session.commit()
            await emit("done", MessageOut.of(msg).model_dump(mode="json"))
        memory.spawn_refresh(conversation_id)
    except Exception as exc:  # noqa: BLE001
        log.exception("Turn failed")
        await emit("error", {"message": redact(f"{type(exc).__name__}: {exc}")[:300]})


async def _teach_turn(conversation_id: uuid.UUID, emit: Emit) -> None:
    """Teaching chat: no retrieval. The assistant restates what it understood and asks clarifying questions."""
    async with SessionLocal() as session:
        rows = (
            await session.execute(
                select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.desc()).limit(20)
            )
        ).scalars().all()
    history = [{"role": m.role, "content": truncate_middle(m.content, 2500)} for m in reversed(rows) if m.meta.get("kind") != "ack"]
    chunks: list[str] = []
    thoughts: list[str] = []
    llm_error = None
    await emit("status", {"step": "generate"})
    try:
        async for channel, piece in get_llm().stream([{"role": "system", "content": TEACH_PROMPT}, *history]):
            if channel == "think":
                thoughts.append(piece)
                await emit("thinking", {"text": piece})
            else:
                chunks.append(piece)
                await emit("token", {"text": piece})
    except LLMError as exc:
        llm_error = str(exc)
        if not chunks:
            chunks.append("⚠️ مدل زبانی در دسترس نیست؛ پیام شما ذخیره شد و همچنان می‌توانید آن را برای تأیید ادمین ارسال کنید.")
            await emit("token", {"text": chunks[0]})
    meta: dict[str, Any] = {"kind": "teach"}
    if thoughts:
        meta["thinking"] = redact("".join(thoughts)).strip()[:30000]
    if llm_error:
        meta["llm_error"] = redact(llm_error)
    async with SessionLocal() as session:
        msg = Message(conversation_id=conversation_id, role="assistant", content=redact("".join(chunks)).strip(), meta=meta)
        session.add(msg)
        convo = await session.get(Conversation, conversation_id)
        if convo is not None:
            convo.updated_at = datetime.now(UTC)
        await session.commit()
        await emit("done", MessageOut.of(msg).model_dump(mode="json"))


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
        convo.state = {"phase": "idle", "attempts": 0, "rejected_refs": [], "failed_summaries": [], "original_problem": None,
                       "memory": memory.set_outcome(state.get("memory"), "confirmed")}
        ack = Message(conversation_id=convo.id, role="assistant", content=CONFIRM_ACK, meta={"kind": "ack"})
        session.add(ack)
        await session.commit()
        await index_solution(sol)
        await bump_kb_version()
        return ack

    # rejected: remember what failed, then ask for the new error output
    await answer_cache.delete(msg.meta.get("answer_cache_key"))  # a rejected answer must not be replayed to anyone
    failed = list(state.get("failed_summaries", []))
    failed.append(truncate_middle(msg.content, 700))
    state.update(
        phase="awaiting_error",
        attempts=int(state.get("attempts", 0)) + 1,
        rejected_refs=sorted(set(state.get("rejected_refs", [])) | set(msg.meta.get("refs", []))),
        failed_summaries=failed[-3:],
        memory=memory.set_outcome(state.get("memory"), "rejected"),
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
        await bump_kb_version()
    except Exception:
        log.exception("Could not remove solution vector %s", solution_id)
