from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from todo_server.app import create_app
from todo_server.config import Settings


@pytest.fixture
def client() -> TestClient:
    settings = Settings(
        version="1.2.3",
        channel="edge",
        timezone=ZoneInfo("Europe/London"),
        host="127.0.0.1",
        port=8000,
    )
    return TestClient(create_app(settings))


def test_index_renders(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Hello, world" in response.text
    assert "1.2.3 (edge)" in response.text


def test_hello_fragment(client: TestClient) -> None:
    response = client.get("/hello")
    assert response.status_code == 200
    assert "Hello from the server" in response.text
    assert "<html" not in response.text


def test_static_htmx_served(client: TestClient) -> None:
    assert client.get("/static/htmx.min.js").status_code == 200


def test_healthz(client: TestClient) -> None:
    assert client.get("/healthz").json() == {"status": "ok"}


def test_version(client: TestClient) -> None:
    assert client.get("/version").json() == {"version": "1.2.3", "channel": "edge"}
