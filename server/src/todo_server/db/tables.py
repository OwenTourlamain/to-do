"""ORM table definitions. Private to the db package: nothing outside it imports these.

Schema changes go through Alembic migrations (db/migrations). After editing a
table here, generate a revision and review it by hand; tests fail if the two
drift apart.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, Index, MetaData, String, Text, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from todo_server.db.types import Json, UtcDateTime, json_default, str_enum
from todo_server.models.enums import (
    Behaviour,
    CompletionKind,
    CompletionSource,
    TaskStatus,
    TriggerKind,
    UserRole,
)

# Deterministic constraint names, which Alembic needs to alter tables on SQLite.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map = {datetime: UtcDateTime, UUID: Uuid, dict[str, Any]: Json}


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    role: Mapped[UserRole] = mapped_column(str_enum(UserRole, "role"))
    timezone: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    deleted_at: Mapped[datetime | None]


class TaskRow(Base):
    __tablename__ = "tasks"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)
    behaviour: Mapped[Behaviour] = mapped_column(str_enum(Behaviour, "behaviour"))
    status: Mapped[TaskStatus] = mapped_column(str_enum(TaskStatus, "status"))
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    deleted_at: Mapped[datetime | None]

    # Relationships also tell the unit of work which rows to insert first.
    creator: Mapped[UserRow] = relationship(lazy="raise")
    triggers: Mapped[list["TriggerRow"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TriggerRow.id",
        lazy="selectin",
    )
    state: Mapped["TaskStateRow | None"] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    __table_args__ = (Index("ix_tasks_status_deleted_at", "status", "deleted_at"),)


class TriggerRow(Base):
    __tablename__ = "task_triggers"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    kind: Mapped[TriggerKind] = mapped_column(str_enum(TriggerKind, "kind"))
    config: Mapped[dict[str, Any]] = mapped_column(default=json_default)
    timezone: Mapped[str | None] = mapped_column(String(64))

    task: Mapped[TaskRow] = relationship(back_populates="triggers")


class TaskStateRow(Base):
    """State the service maintains for a task (as opposed to what the user configured)."""

    __tablename__ = "task_state"

    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    )
    next_due: Mapped[datetime | None] = mapped_column(index=True)
    updated_at: Mapped[datetime]

    task: Mapped[TaskRow] = relationship(back_populates="state")


class CompletionRow(Base):
    """Append-only log of everything done to a task."""

    __tablename__ = "completions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[CompletionKind] = mapped_column(str_enum(CompletionKind, "kind"))
    source: Mapped[CompletionSource] = mapped_column(str_enum(CompletionSource, "source"))
    at: Mapped[datetime]
    note: Mapped[str | None] = mapped_column(Text)

    task: Mapped[TaskRow] = relationship(lazy="raise")
    user: Mapped[UserRow] = relationship(lazy="raise")

    __table_args__ = (Index("ix_completions_task_id_at", "task_id", "at"),)
