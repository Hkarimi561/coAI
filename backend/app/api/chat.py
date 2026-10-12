import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import SessionLocal, get_session
from app.models import Conversation, Lesson, McpServer, Message, User
from app.redis_client import get_redis, rate_limit
from app.schemas import ConversationOut, CreateConversationIn, FeedbackIn, FeedbackOut, LessonOut, MessageOut, SendMessageIn
from app.security import get_current_user
from app.services import ingestion, mcp_command
from app.services.chat_service import run_turn, submit_feedback
from app.services.lessons import submit_lesson

router = APIRouter(prefix="/chat", tags=["chat"])
_background: set[asyncio.Task] = set()  # keep strong refs so turns finish even if the client disconnects


class TurnBuffer:
    """Events of a running turn. Late subscribers (e.g. the user left the page and came back) get a replay, then live events."""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []
        self.subscribers: set[asyncio.Queue[tuple[str, dict[str, Any]] | None]] = set()
        self.finished = False

    def publish(self, event: str, data: dict[str, Any]) -> None:
        last = self.events[-1] if self.events else None
        if last and event in ("token", "thinking") and last[0] == event:  # keep the replay small: merge consecutive text chunks
            self.events[-1] = (event, {"text": last[1]["text"] + data.get("text", "")})
        else:
            self.events.append((event, data))
        for q in self.subscribers:
            q.put_nowait((event, data))

    def finish(self) -> None:
        self.finished = True
        for q in self.subscribers:
            q.put_nowait(None)

    async def follow(self) -> AsyncIterator[str]:
        q: asyncio.Queue[tuple[str, dict[str, Any]] | None] = asyncio.Queue()
        replay = list(self.events)  # snapshot + subscribe without awaiting in between => no gaps, no duplicates
        if not self.finished:
            self.subscribers.add(q)
        try:
            for event, data in replay:
                yield _sse(event, data)
            while not self.finished or not q.empty():
                try:
                    item = await asyncio.wait_for(q.get(), timeout=15)
                except TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                if item is None:
                    break
                yield _sse(*item)
        finally:
            self.subscribers.discard(q)


_turns: dict[uuid.UUID, TurnBuffer] = {}  # running turns by conversation id (single uvicorn worker)


async def get_owned_conversation(session: AsyncSession, user: User, conversation_id: uuid.UUID) -> Conversation:
    convo = await session.get(Conversation, conversation_id)
    if convo is None or (convo.user_id != user.id and user.role != "admin"):
        raise HTTPException(404, "Conversation not found")
    return convo


@router.get("/conversations", response_model=list[ConversationOut])
async def list_conversations(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> list[ConversationOut]:
    rows = (
        await session.execute(
            select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.updated_at.desc()).limit(200)
        )
    ).scalars().all()
    return [ConversationOut.of(c) for c in rows]


@router.post("/conversations", response_model=ConversationOut, status_code=201)
async def create_conversation(
    body: CreateConversationIn | None = None, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)
) -> ConversationOut:
    mode = body.mode if body else "support"
    convo = Conversation(user_id=user.id, title="", state={"phase": "idle"}, mode=mode)
    session.add(convo)
    await session.commit()
    await session.refresh(convo)
    return ConversationOut.of(convo)


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: uuid.UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    convo = await get_owned_conversation(session, user, conversation_id)
    msgs = (
        await session.execute(select(Message).where(Message.conversation_id == convo.id).order_by(Message.created_at, Message.id))
    ).scalars().all()
    return {"conversation": ConversationOut.of(convo), "messages": [MessageOut.of(m) for m in msgs],
            "memory": (convo.state or {}).get("memory"), "active": conversation_id in _turns}


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: uuid.UUID,
    body: SendMessageIn,
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    # short-lived session: the request-scoped one would stay checked out for the whole stream
    async with SessionLocal() as session:
        convo = await get_owned_conversation(session, user, conversation_id)
    if convo.user_id != user.id:
        raise HTTPException(403, "Only the conversation owner can post messages")
    if await ingestion.is_indexing():
        raise HTTPException(503, "Documents are still being indexed; chat is disabled until indexing finishes")
    await rate_limit(f"chat:{user.id}", get_settings().chat_rate_limit_per_minute, 60)

    redis = get_redis()
    lock_key, token = f"turn:{conversation_id}", uuid.uuid4().hex
    if not await redis.set(lock_key, token, nx=True, ex=600):
        raise HTTPException(409, "A response is already being generated for this conversation")

    buf = TurnBuffer()
    _turns[conversation_id] = buf

    async def emit(event: str, data: dict[str, Any]) -> None:
        buf.publish(event, data)

    async def runner() -> None:
        try:
            await run_turn(conversation_id=conversation_id, content=body.content, refresh=body.refresh, emit=emit,
                           user_id=user.id, is_admin=user.role == "admin")
        finally:
            if await redis.get(lock_key) == token:
                await redis.delete(lock_key)
            _turns.pop(conversation_id, None)
            buf.finish()

    task = asyncio.create_task(runner())
    _background.add(task)
    task.add_done_callback(_background.discard)

    return StreamingResponse(
        buf.follow(), media_type="text/event-stream", headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"}
    )


@router.get("/conversations/{conversation_id}/stream")
async def attach_stream(conversation_id: uuid.UUID, user: User = Depends(get_current_user)) -> StreamingResponse:
    """Re-attach to a turn that is still running (replays what was produced so far, then follows live)."""
    async with SessionLocal() as session:
        await get_owned_conversation(session, user, conversation_id)
    buf = _turns.get(conversation_id)
    if buf is None:
        raise HTTPException(404, "No running turn")
    return StreamingResponse(
        buf.follow(), media_type="text/event-stream", headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"}
    )


@router.post("/conversations/{conversation_id}/feedback", response_model=FeedbackOut)
async def feedback(
    conversation_id: uuid.UUID,
    body: FeedbackIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> FeedbackOut:
    convo = await get_owned_conversation(session, user, conversation_id)
    if convo.user_id != user.id:
        raise HTTPException(403, "Only the conversation owner can give feedback")
    new_msg = await submit_feedback(session, user, convo, body.message_id, body.outcome, body.note)
    await session.refresh(convo)
    return FeedbackOut(conversation=ConversationOut.of(convo), message=MessageOut.of(new_msg) if new_msg else None)


@router.post("/conversations/{conversation_id}/lessons", response_model=LessonOut, status_code=201)
async def submit_conversation_lesson(
    conversation_id: uuid.UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)
) -> LessonOut:
    """Send what the user taught the assistant in this teaching chat to the admins for verification."""
    convo = await get_owned_conversation(session, user, conversation_id)
    if convo.user_id != user.id:
        raise HTTPException(403, "Only the conversation owner can submit lessons")
    lesson = await submit_lesson(session, user, convo)
    return LessonOut.of(lesson)


@router.get("/lessons", response_model=list[LessonOut])
async def my_lessons(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> list[LessonOut]:
    rows = (await session.execute(select(Lesson).where(Lesson.user_id == user.id).order_by(Lesson.created_at.desc()).limit(200))).scalars().all()
    return [LessonOut.of(r) for r in rows]


@router.get("/documents/download")
async def download_document(path: str, user: User = Depends(get_current_user)) -> FileResponse:
    """Download an approved Markdown document (the source of an answer) as a .md file."""
    try:
        rel = ingestion.safe_rel_path(path)
    except ingestion.DocsError as exc:
        raise HTTPException(400, str(exc)) from exc
    full = ingestion.docs_root() / rel
    if not full.is_file():
        raise HTTPException(404, "Document not found")
    return FileResponse(full, media_type="text/markdown; charset=utf-8", filename=full.name)


@router.get("/mcp/commands")
async def mcp_commands(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> list[dict[str, Any]]:
    """Slash commands for the message box: enabled MCP servers with a hint and their allow-listed tools (no URLs or headers)."""
    hints = {s.name: s.description for s in (await session.execute(select(McpServer).where(McpServer.enabled.is_(True)))).scalars()}
    out = await mcp_command.available()
    for s in out:
        s["hint"] = hints.get(s["server"]) or ""
    return out
