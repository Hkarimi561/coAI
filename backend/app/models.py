import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _pk() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _now() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _pk()
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default="user")  # admin | user
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = _now()


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    # unresolved | pending_review (user confirmed a fix, admin has not reviewed) | resolved (admin closed / promoted)
    status: Mapped[str] = mapped_column(String(24), default="unresolved", index=True)
    # workflow state: {phase, attempts, rejected_refs, original_problem}
    state: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    mode: Mapped[str] = mapped_column(String(16), default="support")  # support | teach (a user teaching the assistant)
    created_at: Mapped[datetime] = _now()
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=_utcnow, onupdate=_utcnow)

    user: Mapped[User] = relationship(lazy="joined")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = _pk()
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16))  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    citations: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = _now()


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id: Mapped[uuid.UUID] = _pk()
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    message_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    tool: Mapped[str] = mapped_column(String(48))  # docker_logs | ci_status | local_docs | solutions | web_cache | web_search
    input: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    output: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="ok")  # ok | error | skipped
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = _now()


class Solution(Base):
    __tablename__ = "solutions"

    id: Mapped[uuid.UUID] = _pk()
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    problem: Mapped[str] = mapped_column(Text)
    error_signature: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    citations: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(16), default="candidate")  # candidate | promoted | rejected
    document_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = _now()


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = _pk()
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"))
    solution_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("solutions.id", ondelete="SET NULL"), nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    outcome: Mapped[str] = mapped_column(String(16))  # confirmed | rejected
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = _now()


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = _pk()
    path: Mapped[str] = mapped_column(String(512), unique=True)  # relative to DOCS_DIR, posix style
    title: Mapped[str] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(16), default="imported")  # imported | upload | promoted | editor
    content_hash: Mapped[str] = mapped_column(String(64))
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="indexed")  # indexed | error
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = _now()
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=_utcnow, onupdate=_utcnow)


class WebCacheEntry(Base):
    __tablename__ = "web_cache"

    id: Mapped[uuid.UUID] = _pk()
    cache_key: Mapped[str] = mapped_column(String(64), unique=True)
    query_text: Mapped[str] = mapped_column(Text)
    error_signature: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(32))
    results: Mapped[list[Any]] = mapped_column(JSONB, default=list)  # [{title,url,snippet}]
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    hit_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = _now()
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    invalidated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)


class TurnEvent(Base):
    """One row per assistant turn. Source of truth for analytics."""

    __tablename__ = "turn_events"

    id: Mapped[uuid.UUID] = _pk()
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    message_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    query_text: Mapped[str] = mapped_column(Text, default="")
    error_signature: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    signature_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # local_docs | solutions | web_cache | web_fresh | none  -- the stage that supplied the answer
    primary_source: Mapped[str] = mapped_column(String(24), default="none")
    sources: Mapped[list[Any]] = mapped_column(JSONB, default=list)  # distinct kinds actually used (incl. docker/ci)
    web_event: Mapped[str] = mapped_column(String(16), default="none")  # none | cache_hit | coalesced | fresh | failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class AppSetting(Base):
    """Admin-editable runtime switches (web search, GitHub docs, answer cache)."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[Any] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=_utcnow)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)


class Lesson(Base):
    """Knowledge a user taught the assistant in a teaching chat. Only active after an admin approves it."""

    __tablename__ = "lessons"

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    applies_when: Mapped[str] = mapped_column(Text, default="")
    instruction: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)  # pending | approved | rejected
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    review_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = _now()
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(lazy="joined")


class ContainerGrant(Base):
    """Per-user permission on a container (exact name or glob). level: logs (inspect + read logs) | actions (also start/stop/restart)."""

    __tablename__ = "container_grants"

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    container: Mapped[str] = mapped_column(String(64))
    level: Mapped[str] = mapped_column(String(16), default="logs")
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = _now()


class ContainerAudit(Base):
    """Every container action attempt (allowed or denied) made through the UI."""

    __tablename__ = "container_audit"

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    container: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(16))
    result: Mapped[str] = mapped_column(String(300), default="")  # ok | denied | error: ...
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    user: Mapped[User] = relationship(lazy="joined")


class McpServer(Base):
    """Remote MCP server (streamable HTTP or SSE). Only tools listed in `enabled_tools` can ever be called by the assistant."""

    __tablename__ = "mcp_servers"

    id: Mapped[uuid.UUID] = _pk()
    name: Mapped[str] = mapped_column(String(48), unique=True)  # slug, used as tool-name prefix
    transport: Mapped[str] = mapped_column(String(16), default="http")  # http | sse
    url: Mapped[str] = mapped_column(String(500))
    headers: Mapped[dict[str, str]] = mapped_column(JSONB, default=dict)  # e.g. Authorization; never returned by the API
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    tools: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)  # last discovered: name, description, input_schema
    enabled_tools: Mapped[list[str]] = mapped_column(JSONB, default=list)  # admin allow-list (tool names)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = _now()


class Skill(Base):
    """Admin-authored playbook (SKILL.md style). The assistant loads the relevant ones automatically for a question."""

    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = _pk()
    name: Mapped[str] = mapped_column(String(64), unique=True)
    description: Mapped[str] = mapped_column(Text)  # "use when ..." - this is what gets matched against the question
    instructions: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = _now()
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
