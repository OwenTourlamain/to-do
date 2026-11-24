"""Settings read from environment variables."""

import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Settings:
    version: str
    channel: str
    timezone: ZoneInfo
    host: str
    port: int


def load_settings() -> Settings:
    return Settings(
        version=os.environ.get("APP_VERSION", "dev"),
        channel=os.environ.get("RELEASE_CHANNEL", "dev"),
        timezone=ZoneInfo(os.environ.get("APP_TIMEZONE", "Europe/London")),
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
    )
