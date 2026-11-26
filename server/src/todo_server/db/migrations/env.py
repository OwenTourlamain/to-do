"""Alembic environment, used both by the app at startup and by the alembic CLI."""

from logging.config import fileConfig

from alembic import context

from todo_server.config import load_settings
from todo_server.db.engine import build_engine
from todo_server.db.tables import Base

config = context.config
if config.config_file_name and config.attributes.get("connection") is None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)
target_metadata = Base.metadata


def _configure(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,  # SQLite needs batch mode to alter tables
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


connection = config.attributes.get("connection")
if connection is not None:
    _configure(connection)
else:
    url = config.attributes.get("database_url") or load_settings().database_url
    engine = build_engine(url, enforce_foreign_keys=False)
    with engine.connect() as conn:
        _configure(conn)
    engine.dispose()
