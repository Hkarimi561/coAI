"""per-user container permissions and audit log

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-12
"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

NOW = sa.text("now()")


def upgrade() -> None:
    op.create_table(
        "container_grants",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("container", sa.String(64), nullable=False),
        sa.Column("level", sa.String(16), nullable=False, server_default="logs"),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.UniqueConstraint("user_id", "container", name="uq_container_grants_user_container"),
    )
    op.create_index("ix_container_grants_user_id", "container_grants", ["user_id"])
    op.create_table(
        "container_audit",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("container", sa.String(64), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("result", sa.String(300), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_index("ix_container_audit_user_id", "container_audit", ["user_id"])
    op.create_index("ix_container_audit_created_at", "container_audit", ["created_at"])


def downgrade() -> None:
    op.drop_table("container_audit")
    op.drop_table("container_grants")
