"""Repositories: translate between domain models and ORM rows.

Every public method takes and returns domain models from `todo_server.models`;
ORM rows never leave this module.
"""

from collections.abc import Iterable
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from todo_server.db.errors import NotFoundError
from todo_server.db.tables import CompletionRow, TaskRow, TaskStateRow, TriggerRow, UserRow
from todo_server.models import Completion, Task, TaskStatus, Trigger, User

# --- mapping -----------------------------------------------------------------


def _user(row: UserRow) -> User:
    return User(
        id=row.id,
        name=row.name,
        role=row.role,
        timezone=row.timezone,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _trigger(row: TriggerRow) -> Trigger:
    return Trigger(id=row.id, kind=row.kind, config=dict(row.config), timezone=row.timezone)


def _task(row: TaskRow) -> Task:
    return Task(
        id=row.id,
        title=row.title,
        notes=row.notes,
        behaviour=row.behaviour,
        status=row.status,
        created_by=row.created_by,
        created_at=row.created_at,
        updated_at=row.updated_at,
        triggers=tuple(_trigger(t) for t in row.triggers),
        next_due=row.state.next_due if row.state else None,
    )


def _completion(row: CompletionRow) -> Completion:
    return Completion(
        id=row.id,
        task_id=row.task_id,
        user_id=row.user_id,
        kind=row.kind,
        source=row.source,
        at=row.at,
        note=row.note,
    )


def _trigger_row(trigger: Trigger) -> TriggerRow:
    return TriggerRow(
        id=trigger.id,
        kind=trigger.kind,
        config=dict(trigger.config),
        timezone=trigger.timezone,
    )


# --- repositories ------------------------------------------------------------


class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, user: User) -> None:
        self._session.add(
            UserRow(
                id=user.id,
                name=user.name,
                role=user.role,
                timezone=user.timezone,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
        )

    def get(self, user_id: UUID) -> User | None:
        row = self._session.get(UserRow, user_id)
        return _user(row) if row and row.deleted_at is None else None

    def list(self) -> list[User]:
        rows = self._session.scalars(
            select(UserRow).where(UserRow.deleted_at.is_(None)).order_by(UserRow.id)
        )
        return [_user(r) for r in rows]

    def count(self) -> int:
        return self._session.scalar(
            select(func.count()).select_from(UserRow).where(UserRow.deleted_at.is_(None))
        )


class TaskRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, task: Task) -> None:
        row = TaskRow(
            id=task.id,
            title=task.title,
            notes=task.notes,
            behaviour=task.behaviour,
            status=task.status,
            created_by=task.created_by,
            created_at=task.created_at,
            updated_at=task.updated_at,
            triggers=[_trigger_row(t) for t in task.triggers],
            state=TaskStateRow(next_due=task.next_due, updated_at=task.updated_at),
        )
        self._session.add(row)

    def get(self, task_id: UUID) -> Task | None:
        row = self._live_row(task_id)
        return _task(row) if row else None

    def list(self, statuses: Iterable[TaskStatus] | None = None) -> list[Task]:
        """Live tasks, soonest due first; undated tasks last, oldest first."""
        query = (
            select(TaskRow)
            .outerjoin(TaskRow.state)
            .where(TaskRow.deleted_at.is_(None))
            .order_by(TaskStateRow.next_due.asc().nulls_last(), TaskRow.created_at, TaskRow.id)
        )
        if statuses is not None:
            query = query.where(TaskRow.status.in_(list(statuses)))
        return [_task(r) for r in self._session.scalars(query).unique()]

    def update(self, task: Task) -> None:
        """Save every field of `task`, including its triggers and next due time."""
        row = self._live_row(task.id)
        if row is None:
            raise NotFoundError(f"task {task.id}")

        row.title = task.title
        row.notes = task.notes
        row.behaviour = task.behaviour
        row.status = task.status
        row.updated_at = task.updated_at
        self._sync_triggers(row, task.triggers)
        if row.state is None:
            row.state = TaskStateRow(next_due=task.next_due, updated_at=task.updated_at)
        elif row.state.next_due != task.next_due:
            row.state.next_due = task.next_due
            row.state.updated_at = task.updated_at

    def delete(self, task_id: UUID, at: datetime) -> None:
        """Soft delete: the task disappears from reads but stays as a tombstone for sync."""
        row = self._live_row(task_id)
        if row is None:
            raise NotFoundError(f"task {task_id}")
        row.deleted_at = at
        row.updated_at = at

    def _live_row(self, task_id: UUID) -> TaskRow | None:
        row = self._session.get(TaskRow, task_id)
        return row if row and row.deleted_at is None else None

    @staticmethod
    def _sync_triggers(row: TaskRow, triggers: tuple[Trigger, ...]) -> None:
        wanted = {t.id: t for t in triggers}
        for existing in list(row.triggers):
            if existing.id not in wanted:
                row.triggers.remove(existing)
        current = {t.id: t for t in row.triggers}
        for trigger in triggers:
            if trigger.id in current:
                target = current[trigger.id]
                target.kind = trigger.kind
                target.config = dict(trigger.config)
                target.timezone = trigger.timezone
            else:
                row.triggers.append(_trigger_row(trigger))


class CompletionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, completion: Completion) -> None:
        self._session.add(
            CompletionRow(
                id=completion.id,
                task_id=completion.task_id,
                user_id=completion.user_id,
                kind=completion.kind,
                source=completion.source,
                at=completion.at,
                note=completion.note,
            )
        )

    def list_for_task(self, task_id: UUID, limit: int | None = None) -> list[Completion]:
        """Newest first."""
        query = (
            select(CompletionRow)
            .where(CompletionRow.task_id == task_id)
            .order_by(CompletionRow.at.desc(), CompletionRow.id.desc())
            .limit(limit)
        )
        return [_completion(r) for r in self._session.scalars(query)]
