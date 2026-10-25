from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from server import app  # the server.app module (AUTH_TOKEN_ENV, require_auth)
from server.app import app as fastapi_app


def test_auth_accepts_matching_bearer_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(app.AUTH_TOKEN_ENV, "expected")

    app.require_auth("Bearer expected")


@pytest.mark.parametrize("authorization", [None, "Basic expected", "Bearer wrong"])
def test_auth_rejects_missing_or_wrong_token(
    monkeypatch: pytest.MonkeyPatch, authorization: str | None
) -> None:
    monkeypatch.setenv(app.AUTH_TOKEN_ENV, "expected")

    with pytest.raises(HTTPException) as error:
        app.require_auth(authorization)

    assert error.value.status_code == 401


# --- 422 / error responses never echo a secret -----------------------------


class _FakeBackend:
    """DesktopBackend stand-in: records typed secrets without touching X11."""

    def __init__(self, focused_app: str = "browser") -> None:
        self.focused_app = focused_app
        self.typed: list[str] = []

    def active_window(self):
        from friday.desktop.observation import ActiveWindow

        return ActiveWindow(id=None, class_name="Chromium", focused_app=self.focused_app)

    def run_secret_typed(self, argv: list[str], stdin: str) -> None:
        self.typed.append(stdin)


def _client_with(backend: _FakeBackend, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv(app.AUTH_TOKEN_ENV, "expected")
    monkeypatch.setenv("FRIDAY_WORKSPACE", "/tmp/friday-test-workspace")

    from contextlib import contextmanager

    @contextmanager
    def _ctx():
        with TestClient(fastapi_app) as client:
            # the lifespan installs a real backend; swap in the fake per request
            fastapi_app.state.backend = backend
            yield client

    return _ctx()


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "", "value": "hunter2"},
        {"name": "   ", "value": "hunter2"},
        {"name": "db_password"},  # missing value
        {"name": "db_password", "value": "hunter2", "extra": "boom"},  # unknown field
    ],
)
def test_type_secret_422_never_echoes_the_value(
    monkeypatch: pytest.MonkeyPatch, payload: dict[str, object]
) -> None:
    with _client_with(_FakeBackend(), monkeypatch) as client:
        response = client.post(
            "/type_secret", json=payload, headers={"Authorization": "Bearer expected"}
        )

    assert response.status_code == 422
    assert "hunter2" not in response.text


def test_type_secret_types_the_value_when_focus_is_allowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = _FakeBackend(focused_app="browser")
    with _client_with(backend, monkeypatch) as client:
        response = client.post(
            "/type_secret",
            json={"name": "db_password", "value": "hunter2"},
            headers={"Authorization": "Bearer expected"},
        )

    assert response.status_code == 200
    assert backend.typed == ["hunter2"]
    assert "hunter2" not in response.text


@pytest.mark.parametrize("focused_app", ["terminal", "text_editor", "other", "file_manager"])
def test_type_secret_rejects_when_focus_is_not_allowed(
    monkeypatch: pytest.MonkeyPatch, focused_app: str
) -> None:
    backend = _FakeBackend(focused_app=focused_app)
    with _client_with(backend, monkeypatch) as client:
        response = client.post(
            "/type_secret",
            json={"name": "db_password", "value": "hunter2"},
            headers={"Authorization": "Bearer expected"},
        )

    assert response.status_code == 422
    assert backend.typed == []  # nothing was typed
    assert "hunter2" not in response.text
