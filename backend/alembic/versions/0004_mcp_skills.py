"""mcp servers and skills

Revision ID: 0004
Revises: 0003
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

NOW = sa.text("now()")


def upgrade() -> None:
    op.create_table(
        "mcp_servers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(48), nullable=False, unique=True),
        sa.Column("transport", sa.String(16), nullable=False, server_default="http"),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("headers", JSONB(), nullable=False, server_default="{}"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("tools", JSONB(), nullable=False, server_default="[]"),
        sa.Column("enabled_tools", JSONB(), nullable=False, server_default="[]"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_table(
        "skills",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("skills")
    op.drop_table("mcp_servers")
