"""Run Alembic migrations programmatically (no alembic.ini needed at runtime)."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import make_url, text

from todo_server.db.engine import build_engine

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def alembic_config(url: str) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.attributes["database_url"] = url
    return config


def upgrade_to_head(url: str) -> None:
    # Foreign keys stay off while migrating: on SQLite, Alembic's batch mode
    # rebuilds tables by copy-and-drop, and dropping a parent table with
    # enforcement on would cascade-delete its children.
    engine = build_engine(url, enforce_foreign_keys=False)
    try:
        with engine.begin() as connection:
            config = alembic_config(url)
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        if make_url(url).get_backend_name() == "sqlite":
            with engine.connect() as connection:
                problems = connection.execute(text("PRAGMA foreign_key_check")).fetchall()
            if problems:
                raise RuntimeError(f"foreign key violations after migration: {problems}")
    finally:
        engine.dispose()
