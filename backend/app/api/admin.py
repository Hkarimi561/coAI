import asyncio
import re
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Conversation, Document, Feedback, Message, Solution, ToolCall, TurnEvent, User, WebCacheEntry
from app.schemas import ConversationOut, MessageOut, UserCreate, UserOut, UserUpdate
from app.security import hash_password, require_admin
from app.services import analytics, ingestion, promotion
from app.services.chat_service import remove_solution_vector
from app.services.websearch import get_websearch

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _page(page: int, size: int) -> tuple[int, int]:
    return max(page, 1), min(max(size, 1), 100)


def _like(q: str) -> str:
    return "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


# ------------------------------------------------------------------ conversations
@router.get("/conversations")
async def list_conversations(
    page: int = 1,
    page_size: int = 20,
    status: str | None = Query(default=None, pattern="^(resolved|unresolved|pending_review)$"),
    q: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    page, page_size = _page(page, page_size)
    cnt = select(Message.conversation_id.label("cid"), func.count().label("n")).group_by(Message.conversation_id).subquery()
    conds = []
    if status:
        conds.append(Conversation.status == status)
    if q and q.strip():
        like = _like(q.strip())
        conds.append(
            or_(
                Conversation.title.ilike(like, escape="\\"),
                Conversation.user.has(User.email.ilike(like, escape="\\")),
                exists().where(and_(Message.conversation_id == Conversation.id, Message.content.ilike(like, escape="\\"))),
            )
        )
    total = (await session.execute(select(func.count(Conversation.id)).where(*conds))).scalar_one()
    rows = (
        await session.execute(
            select(Conversation, func.coalesce(cnt.c.n, 0))
            .outerjoin(cnt, cnt.c.cid == Conversation.id)
            .where(*conds)
            .order_by(Conversation.updated_at.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
    ).all()
    return {
        "total": total, "page": page, "page_size": page_size,
        "items": [
            {**ConversationOut.of(c).model_dump(mode="json"), "user": {"id": str(c.user.id), "email": c.user.email, "name": c.user.name},
             "message_count": n}
            for c, n in rows
        ],
    }


@router.get("/conversations/{conversation_id}")
async def inspect_conversation(conversation_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    convo = await session.get(Conversation, conversation_id)
    if convo is None:
        raise HTTPException(404, "Conversation not found")

    async def rows(model: Any, order: Any) -> list[Any]:
        return list((await session.execute(select(model).where(model.conversation_id == convo.id).order_by(order))).scalars().all())

    messages = await rows(Message, Message.created_at)
    tool_calls = await rows(ToolCall, ToolCall.created_at)
    feedback = await rows(Feedback, Feedback.created_at)
    solutions = await rows(Solution, Solution.created_at)
    events = await rows(TurnEvent, TurnEvent.created_at)
    return {
        "conversation": ConversationOut.of(convo),
        "user": {"id": str(convo.user.id), "email": convo.user.email, "name": convo.user.name},
        "messages": [MessageOut.of(m) for m in messages],
        "memory": (convo.state or {}).get("memory"),
        "tool_calls": [
            {"id": str(t.id), "message_id": str(t.message_id) if t.message_id else None, "tool": t.tool, "input": t.input,
             "output": t.output, "status": t.status, "duration_ms": t.duration_ms, "created_at": t.created_at}
            for t in tool_calls
        ],
        "feedback": [
            {"id": str(f.id), "message_id": str(f.message_id), "solution_id": str(f.solution_id) if f.solution_id else None,
             "outcome": f.outcome, "note": f.note, "created_at": f.created_at}
            for f in feedback
        ],
        "solutions": [
            {"id": str(s.id), "title": s.title, "status": s.status, "problem": s.problem, "content": s.content,
             "document_id": str(s.document_id) if s.document_id else None, "created_at": s.created_at}
            for s in solutions
        ],
        "turns": [
            {"message_id": str(e.message_id) if e.message_id else None, "primary_source": e.primary_source, "sources": e.sources,
             "web_event": e.web_event, "error_signature": e.error_signature, "signature_text": e.signature_text, "created_at": e.created_at}
            for e in events
        ],
    }


class StatusIn(BaseModel):
    status: str = Field(pattern="^(resolved|unresolved|pending_review)$")


@router.patch("/conversations/{conversation_id}/status", response_model=ConversationOut)
async def set_status(conversation_id: uuid.UUID, body: StatusIn, session: AsyncSession = Depends(get_session)) -> ConversationOut:
    convo = await session.get(Conversation, conversation_id)
    if convo is None:
        raise HTTPException(404, "Conversation not found")
    convo.status = body.status
    await session.commit()
    return ConversationOut.of(convo)


@router.post("/conversations/{conversation_id}/promote/draft")
async def promote_draft(conversation_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    convo = await session.get(Conversation, conversation_id)
    if convo is None:
        raise HTTPException(404, "Conversation not found")
    try:
        return await promotion.draft_document(session, convo)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/solutions/{solution_id}/reject", status_code=204)
async def reject_solution(solution_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> None:
    sol = await session.get(Solution, solution_id)
    if sol is None:
        raise HTTPException(404, "Solution not found")
    sol.status = "rejected"
    await session.commit()
    await remove_solution_vector(sol.id)


# ------------------------------------------------------------------ documents
class DocumentOut(BaseModel):
    id: uuid.UUID
    path: str
    title: str
    source: str
    chunk_count: int
    size_bytes: int
    status: str
    error: str | None
    indexed_at: datetime | None
    updated_at: datetime


def _doc_out(d: Document) -> DocumentOut:
    return DocumentOut(id=d.id, path=d.path, title=d.title, source=d.source, chunk_count=d.chunk_count, size_bytes=d.size_bytes,
                       status=d.status, error=d.error, indexed_at=d.indexed_at, updated_at=d.updated_at)


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents(session: AsyncSession = Depends(get_session)) -> list[DocumentOut]:
    rows = (await session.execute(select(Document).order_by(Document.path))).scalars().all()
    return [_doc_out(d) for d in rows]


@router.get("/documents/{doc_id}")
async def get_document(doc_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    doc = await session.get(Document, doc_id)
    full = ingestion.docs_root() / doc.path if doc else None
    if doc is None or not full or not full.exists():
        raise HTTPException(404, "Document not found")
    content = await asyncio.to_thread(full.read_text, encoding="utf-8")
    return {**_doc_out(doc).model_dump(mode="json"), "content": content}


class PublishIn(BaseModel):
    path: str = Field(min_length=3, max_length=300)
    content: str = Field(min_length=10, max_length=500_000)
    conversation_id: uuid.UUID | None = None
    solution_id: uuid.UUID | None = None
    overwrite: bool = False


@router.post("/documents", response_model=DocumentOut, status_code=201)
async def publish_document(body: PublishIn, admin: User = Depends(require_admin), session: AsyncSession = Depends(get_session)) -> DocumentOut:
    """Approve + publish: writes the Markdown file to the managed docs store and indexes it into Qdrant."""
    content = body.content
    if body.conversation_id:
        content = promotion.with_front_matter(content, promotion.title_of(content, body.path), body.conversation_id, admin.email)
    try:
        doc = await ingestion.save_document(
            session, body.path, content, source="promoted" if body.conversation_id else "editor", overwrite=body.overwrite
        )
    except ingestion.DocsError as exc:
        raise HTTPException(409 if "exists" in str(exc) else 422, str(exc)) from exc
    except Exception as exc:  # embedding / vector store failure: file is saved, indexing can be retried via re-index
        raise HTTPException(502, f"Saved to the docs store but indexing failed: {exc}") from exc

    if body.solution_id:
        sol = await session.get(Solution, body.solution_id)
        if sol:
            sol.status, sol.document_id = "promoted", doc.id
            await remove_solution_vector(sol.id)
    if body.conversation_id:
        convo = await session.get(Conversation, body.conversation_id)
        if convo:
            convo.status = "resolved"
    await session.commit()
    return _doc_out(doc)


class UpdateDocIn(BaseModel):
    content: str = Field(min_length=1, max_length=500_000)


@router.put("/documents/{doc_id}", response_model=DocumentOut)
async def update_document(doc_id: uuid.UUID, body: UpdateDocIn, session: AsyncSession = Depends(get_session)) -> DocumentOut:
    doc = await session.get(Document, doc_id)
    if doc is None:
        raise HTTPException(404, "Document not found")
    try:
        doc = await ingestion.save_document(session, doc.path, body.content, source=doc.source)
    except ingestion.DocsError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Saved but indexing failed: {exc}") from exc
    return _doc_out(doc)


@router.delete("/documents/{doc_id}", status_code=204)
async def delete_document(doc_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> None:
    doc = await session.get(Document, doc_id)
    if doc is None:
        raise HTTPException(404, "Document not found")
    await ingestion.remove_document(session, doc)


@router.post("/documents/upload")
async def upload_documents(files: list[UploadFile] = File(...), session: AsyncSession = Depends(get_session)) -> list[dict[str, Any]]:
    results = []
    for f in files[:50]:
        name = re.sub(r"[^\w.\- ]", "_", (f.filename or "upload.md").split("/")[-1].split("\\")[-1], flags=re.UNICODE)
        try:
            raw = await f.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ingestion.DocsError("File larger than 2 MB")
            if not name.lower().endswith(".md"):
                raise ingestion.DocsError("Only .md files are accepted")
            doc = await ingestion.save_document(session, f"uploads/{name}", raw.decode("utf-8"), source="upload")
            results.append({"filename": name, "ok": True, "chunks": doc.chunk_count})
        except UnicodeDecodeError:
            results.append({"filename": name, "ok": False, "error": "File is not valid UTF-8"})
        except Exception as exc:  # noqa: BLE001
            await session.rollback()
            results.append({"filename": name, "ok": False, "error": str(exc)[:300]})
    return results


@router.post("/documents/reindex")
async def reindex(force: bool = False) -> dict[str, Any]:
    try:
        report = await ingestion.sync_directory(force=force)
    except ingestion.DocsError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"indexed": report.indexed, "skipped": report.skipped, "removed": report.removed, "errors": report.errors}


# ------------------------------------------------------------------ web cache
@router.get("/cache")
async def list_cache(
    page: int = 1, page_size: int = 20, q: str | None = None, include_invalidated: bool = False, session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    page, page_size = _page(page, page_size)
    conds = []
    if not include_invalidated:
        conds.append(WebCacheEntry.invalidated_at.is_(None))
    if q and q.strip():
        like = _like(q.strip())
        conds.append(or_(WebCacheEntry.query_text.ilike(like, escape="\\"), WebCacheEntry.error_signature.ilike(like, escape="\\")))
    total = (await session.execute(select(func.count(WebCacheEntry.id)).where(*conds))).scalar_one()
    rows = (
        await session.execute(
            select(WebCacheEntry).where(*conds).order_by(WebCacheEntry.created_at.desc()).limit(page_size).offset((page - 1) * page_size)
        )
    ).scalars().all()
    return {
        "total": total, "page": page, "page_size": page_size,
        "items": [
            {"id": str(e.id), "cache_key": e.cache_key, "query_text": e.query_text, "error_signature": e.error_signature,
             "provider": e.provider, "result_count": len(e.results or []), "hit_count": e.hit_count, "has_answer": bool(e.answer),
             "created_at": e.created_at, "expires_at": e.expires_at, "invalidated_at": e.invalidated_at}
            for e in rows
        ],
    }


@router.get("/cache/{entry_id}")
async def get_cache_entry(entry_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    e = await session.get(WebCacheEntry, entry_id)
    if e is None:
        raise HTTPException(404, "Cache entry not found")
    return {"id": str(e.id), "cache_key": e.cache_key, "query_text": e.query_text, "error_signature": e.error_signature,
            "provider": e.provider, "results": e.results, "answer": e.answer, "hit_count": e.hit_count,
            "created_at": e.created_at, "expires_at": e.expires_at, "invalidated_at": e.invalidated_at}


@router.post("/cache/{entry_id}/invalidate", status_code=204)
async def invalidate_cache_entry(entry_id: uuid.UUID, admin: User = Depends(require_admin)) -> None:
    if not await get_websearch().invalidate(entry_id, admin.id):
        raise HTTPException(404, "Cache entry not found")


# ------------------------------------------------------------------ analytics
@router.get("/analytics")
async def get_analytics(days: int = Query(default=30, ge=1, le=365), session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    return await analytics.compute(session, days)


# ------------------------------------------------------------------ users
@router.get("/users", response_model=list[UserOut])
async def list_users(session: AsyncSession = Depends(get_session)) -> list[User]:
    return list((await session.execute(select(User).order_by(User.created_at))).scalars().all())


@router.post("/users", response_model=UserOut, status_code=201)
async def create_user(body: UserCreate, session: AsyncSession = Depends(get_session)) -> User:
    user = User(email=body.email.strip().lower(), name=body.name.strip(), password_hash=hash_password(body.password), role=body.role)
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(409, "A user with this e-mail already exists") from None
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID, body: UserUpdate, admin: User = Depends(require_admin), session: AsyncSession = Depends(get_session)
) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    if user.id == admin.id and (body.is_active is False or (body.role and body.role != "admin")):
        raise HTTPException(409, "You cannot disable or demote your own account")
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.role:
        user.role = body.role
    if body.password:
        user.password_hash = hash_password(body.password)
    await session.commit()
    return user
