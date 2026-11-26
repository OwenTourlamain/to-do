from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from todo_server.app import create_app
from todo_server.config import Settings


def make_client(channel: str = "edge") -> TestClient:
    settings = Settings(
        version="1.2.3",
        channel=channel,
        timezone=ZoneInfo("Europe/London"),
        host="127.0.0.1",
        port=8000,
    )
    return TestClient(create_app(settings))


@pytest.fixture
def client() -> TestClient:
    return make_client()


def test_index_renders(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Hello world again!" in response.text
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


@pytest.mark.parametrize("channel", ["dev", "edge", "ci"])
def test_env_badge_shown_outside_stable(channel: str) -> None:
    html = make_client(channel).get("/").text
    assert 'data-testid="env-badge"' in html
    assert f"<summary>{channel.upper()}</summary>" in html


def test_env_badge_hidden_on_stable() -> None:
    html = make_client("stable").get("/").text
    assert "env-badge" not in html


def test_stylesheet_served(client: TestClient) -> None:
    assert client.get("/static/app.css").status_code == 200
