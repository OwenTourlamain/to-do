"""Portable column types."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, DateTime, Dialect, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator


class UtcDateTime(TypeDecorator[datetime]):
    """Timezone-aware UTC datetimes on every backend.

    Naive datetimes are rejected on write, so a missing timezone is caught at
    the boundary instead of silently stored. Values always come back aware, in UTC.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"naive datetime not allowed: {value!r}")
        return value.astimezone(UTC)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


# JSON everywhere, JSONB on PostgreSQL.
Json = JSON().with_variant(JSONB(), "postgresql")


def str_enum(enum_cls: type[StrEnum], name: str) -> Enum:
    """A StrEnum stored as its value in a VARCHAR with a CHECK constraint (no native enums)."""
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=32,
        values_callable=lambda members: [m.value for m in members],
        validate_strings=True,
    )


def json_default() -> dict[str, Any]:
    return {}
