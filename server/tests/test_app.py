from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient


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


def test_static_files_served(client: TestClient) -> None:
    assert client.get("/static/htmx.min.js").status_code == 200
    assert client.get("/static/app.css").status_code == 200


def test_healthz(client: TestClient) -> None:
    assert client.get("/healthz").json() == {"status": "ok"}


def test_version(client: TestClient) -> None:
    assert client.get("/version").json() == {"version": "1.2.3", "channel": "edge"}


@pytest.mark.parametrize("channel", ["dev", "edge", "ci"])
def test_env_badge_shown_outside_stable(
    make_client: Callable[..., TestClient], channel: str
) -> None:
    html = make_client(channel).get("/").text
    assert 'data-testid="env-badge"' in html
    assert f"<summary>{channel.upper()}</summary>" in html


def test_env_badge_hidden_on_stable(make_client: Callable[..., TestClient]) -> None:
    html = make_client("stable").get("/").text
    assert "env-badge" not in html


def test_startup_migrates_and_creates_default_user(client: TestClient) -> None:
    with client.app.state.db.unit_of_work() as uow:
        users = uow.users.list()
    assert [u.name for u in users] == ["Owner"]
