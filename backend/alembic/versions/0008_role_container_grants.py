"""container access granted through roles

Revision ID: 0008
Revises: 0007
"""
import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "role_container_grants",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("role_id", sa.Uuid(), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("container", sa.String(64), nullable=False),
        sa.Column("level", sa.String(16), nullable=False, server_default="logs"),
        sa.UniqueConstraint("role_id", "container", name="uq_role_container_grants_role_container"),
    )
    op.create_index("ix_role_container_grants_role_id", "role_container_grants", ["role_id"])


def downgrade() -> None:
    op.drop_table("role_container_grants")
