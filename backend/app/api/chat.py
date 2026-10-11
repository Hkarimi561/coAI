import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import SessionLocal, get_session
from app.models import Conversation, Message, User
from app.redis_client import get_redis, rate_limit
from app.schemas import ConversationOut, FeedbackIn, FeedbackOut, MessageOut, SendMessageIn
from app.security import get_current_user
from app.services.chat_service import run_turn, submit_feedback

router = APIRouter(prefix="/chat", tags=["chat"])
_background: set[asyncio.Task] = set()  # keep strong refs so turns finish even if the client disconnects


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
async def create_conversation(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> ConversationOut:
    convo = Conversation(user_id=user.id, title="", state={"phase": "idle"})
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
    return {"conversation": ConversationOut.of(convo), "messages": [MessageOut.of(m) for m in msgs]}


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
    await rate_limit(f"chat:{user.id}", get_settings().chat_rate_limit_per_minute, 60)

    redis = get_redis()
    lock_key, token = f"turn:{conversation_id}", uuid.uuid4().hex
    if not await redis.set(lock_key, token, nx=True, ex=600):
        raise HTTPException(409, "A response is already being generated for this conversation")

    queue: asyncio.Queue[tuple[str, dict[str, Any]] | None] = asyncio.Queue()

    async def emit(event: str, data: dict[str, Any]) -> None:
        await queue.put((event, data))

    async def runner() -> None:
        try:
            await run_turn(conversation_id=conversation_id, content=body.content, emit=emit)
        finally:
            if await redis.get(lock_key) == token:
                await redis.delete(lock_key)
            await queue.put(None)

    task = asyncio.create_task(runner())
    _background.add(task)
    task.add_done_callback(_background.discard)

    async def stream() -> AsyncIterator[str]:
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=15)
            except TimeoutError:
                yield ": keep-alive\n\n"
                continue
            if item is None:
                break
            yield _sse(*item)

    return StreamingResponse(
        stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"}
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
