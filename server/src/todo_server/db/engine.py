"""Engine construction, including per-backend connection setup."""

from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event, make_url


def build_engine(url: str, *, enforce_foreign_keys: bool = True) -> Engine:
    parsed = make_url(url)
    if parsed.get_backend_name() != "sqlite":
        return create_engine(url)

    if parsed.database and parsed.database != ":memory:":
        Path(parsed.database).parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(url)

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection: Any, _record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute(f"PRAGMA foreign_keys={'ON' if enforce_foreign_keys else 'OFF'}")
        cursor.close()

    return engine
