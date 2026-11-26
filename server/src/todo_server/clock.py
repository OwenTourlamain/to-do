"""The current time. Services take `now` as an argument; this is where it comes from."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)
