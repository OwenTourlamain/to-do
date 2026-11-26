"""Domain entities: plain, immutable dataclasses with no knowledge of storage.

Change one with `dataclasses.replace(entity, field=value)`. All datetimes are
timezone-aware and in UTC.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from todo_server.models.enums import (
    Behaviour,
    CompletionKind,
    CompletionSource,
    TaskStatus,
    TriggerKind,
    UserRole,
)


@dataclass(frozen=True, kw_only=True)
class User:
    id: UUID
    name: str
    role: UserRole
    timezone: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, kw_only=True)
class Trigger:
    """One thing that can make a task due. `config` depends on `kind`."""

    id: UUID
    kind: TriggerKind
    config: dict[str, Any] = field(default_factory=dict)
    timezone: str | None = None


@dataclass(frozen=True, kw_only=True)
class Task:
    id: UUID
    title: str
    notes: str | None
    behaviour: Behaviour
    status: TaskStatus
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    triggers: tuple[Trigger, ...] = ()
    next_due: datetime | None = None


@dataclass(frozen=True, kw_only=True)
class Completion:
    id: UUID
    task_id: UUID
    user_id: UUID
    kind: CompletionKind
    source: CompletionSource
    at: datetime
    note: str | None = None
