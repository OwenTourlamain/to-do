"""Settings read from environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo


@dataclass(frozen=True, kw_only=True)
class Settings:
    version: str
    channel: str
    timezone: ZoneInfo
    host: str
    port: int
    database_url: str


def load_settings() -> Settings:
    data_dir = Path(os.environ.get("DATA_DIR", "./data"))
    return Settings(
        version=os.environ.get("APP_VERSION", "dev"),
        channel=os.environ.get("RELEASE_CHANNEL", "dev"),
        timezone=ZoneInfo(os.environ.get("APP_TIMEZONE", "Europe/London")),
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
        database_url=os.environ.get("DATABASE_URL", f"sqlite:///{data_dir.resolve()}/todo.db"),
    )
