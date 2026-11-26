from collections.abc import Callable, Iterator
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from todo_server.app import create_app
from todo_server.config import Settings
from todo_server.db import Database


@pytest.fixture
def database_url(tmp_path: Path) -> str:
    return f"sqlite:///{tmp_path}/test.db"


@pytest.fixture
def database(database_url: str) -> Iterator[Database]:
    db = Database(database_url)
    db.migrate()
    yield db
    db.close()


@pytest.fixture
def make_client(database_url: str) -> Iterator[Callable[..., TestClient]]:
    clients: list[TestClient] = []

    def _make(channel: str = "edge") -> TestClient:
        settings = Settings(
            version="1.2.3",
            channel=channel,
            timezone=ZoneInfo("Europe/London"),
            host="127.0.0.1",
            port=8000,
            database_url=database_url,
        )
        client = TestClient(create_app(settings))
        client.__enter__()  # runs the lifespan: migrations and bootstrap
        clients.append(client)
        return client

    yield _make
    for client in clients:
        client.__exit__(None, None, None)


@pytest.fixture
def client(make_client: Callable[..., TestClient]) -> TestClient:
    return make_client()
