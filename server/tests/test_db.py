"""The db package, tested only through its public facade."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone

import pytest
from alembic import command

from todo_server.db import ConstraintViolation, Database, NotFoundError
from todo_server.db.migrate import alembic_config
from todo_server.ids import uuid7
from todo_server.models import (
    Behaviour,
    Completion,
    CompletionKind,
    CompletionSource,
    Task,
    TaskStatus,
    Trigger,
    TriggerKind,
    User,
    UserRole,
)
from todo_server.services.bootstrap import ensure_default_user

NOW = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)


def make_user(**overrides: object) -> User:
    fields: dict[str, object] = dict(
        id=uuid7(),
        name="Owen",
        role=UserRole.ADMIN,
        timezone="Europe/London",
        created_at=NOW,
        updated_at=NOW,
    )
    return User(**(fields | overrides))  # type: ignore[arg-type]


def make_task(created_by: User, **overrides: object) -> Task:
    fields: dict[str, object] = dict(
        id=uuid7(),
        title="Post and bins",
        notes=None,
        behaviour=Behaviour.ONCE,
        status=TaskStatus.ACTIVE,
        created_by=created_by.id,
        created_at=NOW,
        updated_at=NOW,
    )
    return Task(**(fields | overrides))  # type: ignore[arg-type]


@pytest.fixture
def user(database: Database) -> User:
    user = make_user()
    with database.unit_of_work() as uow:
        uow.users.add(user)
    return user


# --- migrations ----------------------------------------------------------------


def test_migrations_are_idempotent(database: Database) -> None:
    database.migrate()  # already at head from the fixture; must be a no-op


def test_tables_match_migrations(database: Database, database_url: str) -> None:
    """Fails if tables.py was changed without a migration (or the reverse)."""
    command.check(alembic_config(database_url))


# --- users -----------------------------------------------------------------------


def test_user_round_trip(database: Database, user: User) -> None:
    with database.unit_of_work() as uow:
        assert uow.users.get(user.id) == user
        assert uow.users.count() == 1


def test_default_user_created_once(database: Database) -> None:
    with database.unit_of_work() as uow:
        first = ensure_default_user(uow, now=NOW, timezone="Europe/London")
    with database.unit_of_work() as uow:
        second = ensure_default_user(uow, now=NOW, timezone="Europe/London")
        assert uow.users.count() == 1
    assert first == second
    assert first.role is UserRole.ADMIN


# --- tasks -----------------------------------------------------------------------


def test_task_round_trip_with_trigger_and_due(database: Database, user: User) -> None:
    due = NOW + timedelta(days=1)
    task = make_task(
        user,
        notes="Black bags",
        triggers=(Trigger(id=uuid7(), kind=TriggerKind.AT, config={"at": due.isoformat()}),),
        next_due=due,
    )
    with database.unit_of_work() as uow:
        uow.tasks.add(task)
    with database.unit_of_work() as uow:
        assert uow.tasks.get(task.id) == task


def test_datetimes_come_back_aware_utc(database: Database, user: User) -> None:
    due = datetime(2026, 7, 1, 9, 0, tzinfo=timezone(timedelta(hours=1)))  # 08:00 UTC
    task = make_task(user, next_due=due)
    with database.unit_of_work() as uow:
        uow.tasks.add(task)
    with database.unit_of_work() as uow:
        stored = uow.tasks.get(task.id)
    assert stored is not None and stored.next_due is not None
    assert stored.next_due.tzinfo is UTC
    assert stored.next_due == datetime(2026, 7, 1, 8, 0, tzinfo=UTC)


def test_naive_datetimes_rejected(database: Database, user: User) -> None:
    task = make_task(user, next_due=datetime(2026, 7, 1, 9, 0))
    with pytest.raises(Exception, match="naive datetime"), database.unit_of_work() as uow:
        uow.tasks.add(task)


def test_update_changes_fields_triggers_and_due(database: Database, user: User) -> None:
    keep = Trigger(id=uuid7(), kind=TriggerKind.AT, config={"at": "a"})
    drop = Trigger(id=uuid7(), kind=TriggerKind.EVENT, config={"key": "x"})
    task = make_task(user, triggers=(keep, drop), next_due=NOW)
    with database.unit_of_work() as uow:
        uow.tasks.add(task)

    added = Trigger(id=uuid7(), kind=TriggerKind.EVENT, config={"key": "y"})
    changed = replace(
        task,
        title="Bins",
        status=TaskStatus.DONE,
        triggers=(replace(keep, config={"at": "b"}), added),
        next_due=None,
        updated_at=NOW + timedelta(hours=1),
    )
    with database.unit_of_work() as uow:
        uow.tasks.update(changed)
    with database.unit_of_work() as uow:
        assert uow.tasks.get(task.id) == changed


def test_update_missing_task_raises(database: Database, user: User) -> None:
    with pytest.raises(NotFoundError), database.unit_of_work() as uow:
        uow.tasks.update(make_task(user))


def test_soft_delete_hides_task(database: Database, user: User) -> None:
    task = make_task(user)
    with database.unit_of_work() as uow:
        uow.tasks.add(task)
    with database.unit_of_work() as uow:
        uow.tasks.delete(task.id, at=NOW)
    with database.unit_of_work() as uow:
        assert uow.tasks.get(task.id) is None
        assert uow.tasks.list() == []
    with pytest.raises(NotFoundError), database.unit_of_work() as uow:
        uow.tasks.delete(task.id, at=NOW)


def test_list_orders_by_due_with_undated_last(database: Database, user: User) -> None:
    undated_old = make_task(user, title="undated old")
    later = make_task(user, title="later", next_due=NOW + timedelta(days=2))
    sooner = make_task(user, title="sooner", next_due=NOW + timedelta(days=1))
    undated_new = make_task(user, title="undated new")
    with database.unit_of_work() as uow:
        for task in (undated_old, later, sooner, undated_new):
            uow.tasks.add(task)
    with database.unit_of_work() as uow:
        titles = [t.title for t in uow.tasks.list()]
    assert titles == ["sooner", "later", "undated old", "undated new"]


def test_list_filters_by_status(database: Database, user: User) -> None:
    active = make_task(user, title="active")
    done = make_task(user, title="done", status=TaskStatus.DONE)
    with database.unit_of_work() as uow:
        uow.tasks.add(active)
        uow.tasks.add(done)
    with database.unit_of_work() as uow:
        assert [t.title for t in uow.tasks.list([TaskStatus.DONE])] == ["done"]


# --- completions -------------------------------------------------------------------


def test_completions_newest_first(database: Database, user: User) -> None:
    task = make_task(user)

    def completion(at: datetime, kind: CompletionKind) -> Completion:
        return Completion(
            id=uuid7(),
            task_id=task.id,
            user_id=user.id,
            kind=kind,
            source=CompletionSource.WEB,
            at=at,
        )

    older = completion(NOW, CompletionKind.DONE)
    newer = completion(NOW + timedelta(hours=1), CompletionKind.SKIPPED)
    with database.unit_of_work() as uow:
        uow.tasks.add(task)
        uow.completions.add(older)
        uow.completions.add(newer)
    with database.unit_of_work() as uow:
        assert uow.completions.list_for_task(task.id) == [newer, older]
        assert uow.completions.list_for_task(task.id, limit=1) == [newer]


# --- transactions and constraints ---------------------------------------------------


def test_failed_unit_of_work_rolls_back(database: Database, user: User) -> None:
    task = make_task(user)
    with pytest.raises(RuntimeError), database.unit_of_work() as uow:
        uow.tasks.add(task)
        raise RuntimeError("boom")
    with database.unit_of_work() as uow:
        assert uow.tasks.get(task.id) is None


def test_foreign_keys_enforced(database: Database) -> None:
    orphan = make_task(make_user())  # creator never saved
    with pytest.raises(ConstraintViolation), database.unit_of_work() as uow:
        uow.tasks.add(orphan)


def test_check_constraints_enforced(database: Database, user: User) -> None:
    from sqlalchemy import text

    from todo_server.db.engine import build_engine  # test-only peek below the facade

    engine = build_engine(str(database._url))  # noqa: SLF001
    with pytest.raises(Exception, match="CHECK constraint failed"), engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO tasks (id, title, behaviour, status, created_by, created_at,"
                " updated_at) VALUES (:id, 't', 'bogus', 'active', :u, :n, :n)"
            ),
            {"id": uuid7().hex, "u": user.id.hex, "n": "2026-11-26 12:00:00"},
        )
    engine.dispose()
