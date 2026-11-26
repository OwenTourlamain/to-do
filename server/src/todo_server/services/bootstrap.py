"""First-run setup."""

from datetime import datetime

from todo_server.db import UnitOfWork
from todo_server.ids import uuid7
from todo_server.models import User, UserRole

DEFAULT_USER_NAME = "Owner"


def ensure_default_user(uow: UnitOfWork, *, now: datetime, timezone: str) -> User:
    """Until accounts exist, everything belongs to one built-in admin user.

    Creates it on first run; afterwards returns the first user.
    """
    users = uow.users.list()
    if users:
        return users[0]
    user = User(
        id=uuid7(),
        name=DEFAULT_USER_NAME,
        role=UserRole.ADMIN,
        timezone=timezone,
        created_at=now,
        updated_at=now,
    )
    uow.users.add(user)
    return user
