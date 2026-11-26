"""The db package's public entry point: a Database and its units of work."""

from types import TracebackType
from typing import Self

from sqlalchemy import exc
from sqlalchemy.orm import Session, sessionmaker

from todo_server.db import migrate
from todo_server.db.engine import build_engine
from todo_server.db.errors import ConstraintViolation
from todo_server.db.repositories import CompletionRepository, TaskRepository, UserRepository


class UnitOfWork:
    """One transaction. Commits when the `with` block succeeds, rolls back if it raises.

    with database.unit_of_work() as uow:
        uow.tasks.add(task)
    """

    users: UserRepository
    tasks: TaskRepository
    completions: CompletionRepository

    def __init__(self, session: Session) -> None:
        self._session = session
        self.users = UserRepository(session)
        self.tasks = TaskRepository(session)
        self.completions = CompletionRepository(session)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            if exc_type is None:
                self._session.commit()
            else:
                self._session.rollback()
        except exc.IntegrityError as error:
            self._session.rollback()
            raise ConstraintViolation(str(error.orig)) from error
        finally:
            self._session.close()
        if isinstance(exc_value, exc.IntegrityError):
            raise ConstraintViolation(str(exc_value.orig)) from exc_value


class Database:
    """A connection to the datastore, configured from a URL.

    Callers need nothing else from this package: `migrate()` once at startup,
    then `unit_of_work()` for each piece of work.
    """

    def __init__(self, url: str) -> None:
        self._url = url
        self._engine = build_engine(url)
        self._sessions = sessionmaker(self._engine, expire_on_commit=False)

    def migrate(self) -> None:
        """Bring the schema up to the latest version. Safe to run on every start."""
        migrate.upgrade_to_head(self._url)

    def unit_of_work(self) -> UnitOfWork:
        return UnitOfWork(self._sessions())

    def close(self) -> None:
        self._engine.dispose()
