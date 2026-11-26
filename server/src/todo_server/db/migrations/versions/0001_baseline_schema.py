"""Baseline schema: users, tasks, task_triggers, task_state, completions.

Revision ID: 0001
Revises:
Created: 2026-11-26 21:08:51.996391
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

import todo_server.db.types

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "admin", "member", name="role", native_enum=False, create_constraint=True, length=32
            ),
            nullable=False,
        ),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("created_at", todo_server.db.types.UtcDateTime(timezone=True), nullable=False),
        sa.Column("updated_at", todo_server.db.types.UtcDateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", todo_server.db.types.UtcDateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "behaviour",
            sa.Enum(
                "once",
                "recurring",
                "habit",
                "someday",
                name="behaviour",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "active",
                "waiting",
                "done",
                "archived",
                name="status",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", todo_server.db.types.UtcDateTime(timezone=True), nullable=False),
        sa.Column("updated_at", todo_server.db.types.UtcDateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", todo_server.db.types.UtcDateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name=op.f("fk_tasks_created_by_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tasks")),
    )
    with op.batch_alter_table("tasks", schema=None) as batch_op:
        batch_op.create_index("ix_tasks_status_deleted_at", ["status", "deleted_at"], unique=False)

    op.create_table(
        "completions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "done",
                "skipped",
                "missed",
                "progress",
                name="kind",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.Enum(
                "app",
                "web",
                "mcp",
                "ha",
                "api",
                "system",
                name="source",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("at", todo_server.db.types.UtcDateTime(timezone=True), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["task_id"], ["tasks.id"], name=op.f("fk_completions_task_id_tasks"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_completions_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_completions")),
    )
    with op.batch_alter_table("completions", schema=None) as batch_op:
        batch_op.create_index("ix_completions_task_id_at", ["task_id", "at"], unique=False)

    op.create_table(
        "task_state",
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("next_due", todo_server.db.types.UtcDateTime(timezone=True), nullable=True),
        sa.Column("updated_at", todo_server.db.types.UtcDateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["task_id"], ["tasks.id"], name=op.f("fk_task_state_task_id_tasks"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("task_id", name=op.f("pk_task_state")),
    )
    with op.batch_alter_table("task_state", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_task_state_next_due"), ["next_due"], unique=False)

    op.create_table(
        "task_triggers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "at",
                "after_completion",
                "schedule",
                "event",
                name="kind",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "config",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("timezone", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name=op.f("fk_task_triggers_task_id_tasks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_task_triggers")),
    )
    with op.batch_alter_table("task_triggers", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_task_triggers_task_id"), ["task_id"], unique=False)


def downgrade() -> None:
    raise NotImplementedError("Migrations are forward-only.")
