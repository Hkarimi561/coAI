"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-10-11
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

JSONB = postgresql.JSONB(astext_type=sa.Text())
NOW = sa.text("now()")


def _id() -> sa.Column:
    return sa.Column("id", sa.Uuid(), primary_key=True)


def _created() -> sa.Column:
    return sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False)


def upgrade() -> None:
    op.create_table(
        "users",
        _id(),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(16), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        _created(),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "conversations",
        _id(),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False, server_default=""),
        sa.Column("status", sa.String(24), nullable=False, server_default="unresolved"),
        sa.Column("state", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        _created(),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])
    op.create_index("ix_conversations_status", "conversations", ["status"])

    op.create_table(
        "messages",
        _id(),
        sa.Column("conversation_id", sa.Uuid(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("meta", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        _created(),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])

    op.create_table(
        "tool_calls",
        _id(),
        sa.Column("conversation_id", sa.Uuid(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message_id", sa.Uuid(), sa.ForeignKey("messages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tool", sa.String(48), nullable=False),
        sa.Column("input", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("output", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(16), nullable=False, server_default="ok"),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        _created(),
    )
    op.create_index("ix_tool_calls_conversation_id", "tool_calls", ["conversation_id"])

    op.create_table(
        "documents",
        _id(),
        sa.Column("path", sa.String(512), nullable=False, unique=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("source", sa.String(16), nullable=False, server_default="imported"),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False, server_default="indexed"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
        _created(),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )

    op.create_table(
        "solutions",
        _id(),
        sa.Column("conversation_id", sa.Uuid(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message_id", sa.Uuid(), sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("problem", sa.Text(), nullable=False),
        sa.Column("error_signature", sa.String(64), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(16), nullable=False, server_default="candidate"),
        sa.Column("document_id", sa.Uuid(), sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True),
        _created(),
    )
    op.create_index("ix_solutions_conversation_id", "solutions", ["conversation_id"])
    op.create_index("ix_solutions_error_signature", "solutions", ["error_signature"])

    op.create_table(
        "feedback",
        _id(),
        sa.Column("conversation_id", sa.Uuid(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message_id", sa.Uuid(), sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("solution_id", sa.Uuid(), sa.ForeignKey("solutions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("outcome", sa.String(16), nullable=False),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        _created(),
    )
    op.create_index("ix_feedback_conversation_id", "feedback", ["conversation_id"])

    op.create_table(
        "web_cache",
        _id(),
        sa.Column("cache_key", sa.String(64), nullable=False, unique=True),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("error_signature", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("results", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("hit_count", sa.Integer(), nullable=False, server_default="0"),
        _created(),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidated_by", sa.Uuid(), nullable=True),
    )

    op.create_table(
        "turn_events",
        _id(),
        sa.Column("conversation_id", sa.Uuid(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message_id", sa.Uuid(), sa.ForeignKey("messages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("query_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("error_signature", sa.String(64), nullable=True),
        sa.Column("signature_text", sa.Text(), nullable=True),
        sa.Column("primary_source", sa.String(24), nullable=False, server_default="none"),
        sa.Column("sources", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("web_event", sa.String(16), nullable=False, server_default="none"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_index("ix_turn_events_conversation_id", "turn_events", ["conversation_id"])
    op.create_index("ix_turn_events_error_signature", "turn_events", ["error_signature"])
    op.create_index("ix_turn_events_created_at", "turn_events", ["created_at"])


def downgrade() -> None:
    for table in ("turn_events", "web_cache", "feedback", "solutions", "documents", "tool_calls", "messages", "conversations", "users"):
        op.drop_table(table)
