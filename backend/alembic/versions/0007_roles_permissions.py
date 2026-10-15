"""roles and permissions (users have many roles, roles have many permissions)

Revision ID: 0007
Revises: 0006
"""
import uuid

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

NOW = sa.text("now()")

# snapshot of app.permissions.CATALOG at the time of this migration (the app re-syncs the admin role on every start)
ADMIN_PERMISSIONS = [
    "system.view", "analytics.view", "documents.manage", "skills.manage", "lessons.review", "gaps.view", "cache.manage",
    "mcp.manage", "containers.logs_all", "containers.actions_all", "containers.manage_access",
    "conversations.view_all", "conversations.manage", "users.manage", "roles.manage", "settings.manage",
]


def upgrade() -> None:
    roles = op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(48), nullable=False, unique=True),
        sa.Column("description", sa.String(200), nullable=False, server_default=""),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    role_permissions = op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Uuid(), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission", sa.String(64), primary_key=True),
    )
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.Uuid(), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])

    admin_id, user_id = uuid.uuid4(), uuid.uuid4()
    op.bulk_insert(roles, [
        {"id": admin_id, "name": "admin", "description": "Full access to everything", "is_system": True},
        {"id": user_id, "name": "user", "description": "Default role: can chat with the assistant", "is_system": True},
    ])
    op.bulk_insert(role_permissions, [{"role_id": admin_id, "permission": p} for p in ADMIN_PERMISSIONS])

    # carry the old single `users.role` over, then drop it
    op.execute("INSERT INTO user_roles (user_id, role_id) SELECT u.id, r.id FROM users u JOIN roles r ON r.name = u.role")
    op.drop_column("users", "role")


def downgrade() -> None:
    op.add_column("users", sa.Column("role", sa.String(16), nullable=False, server_default="user"))
    op.execute(
        "UPDATE users SET role = 'admin' WHERE id IN "
        "(SELECT ur.user_id FROM user_roles ur JOIN roles r ON r.id = ur.role_id WHERE r.name = 'admin')"
    )
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("roles")
