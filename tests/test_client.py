from __future__ import annotations

import httpx
import pytest

from friday.actions.models import MouseMoveAction
from friday.desktop.client import DesktopClient
from friday.desktop.errors import (
    DesktopConnectionError,
    DesktopRequestError,
    DesktopTimeoutError,
)
from friday.sandbox.base import Sandbox


class FakeSandbox(Sandbox):
    @property
    def api_url(self) -> str:
        return "http://desktop.test"

    @property
    def viewer_url(self) -> str:
        return "http://viewer.test"

    @property
    def token(self) -> str:
        return "secret"

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def wait_until_ready(self) -> None:
        pass


def test_client_sends_auth_and_returns_desktop_data() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path == "/screenshot":
            return httpx.Response(200, content=b"\x89PNG\r\n\x1a\n")
        if request.url.path == "/screen_size":
            return httpx.Response(200, json={"width": 1280, "height": 720})
        if request.url.path == "/cursor":
            return httpx.Response(200, json={"x": 2, "y": 3})
        if request.url.path == "/active_window":
            return httpx.Response(
                200, json={"id": "0x00000001", "class_name": "Chromium", "focused_app": "browser"}
            )
        if request.url.path == "/observation":
            return httpx.Response(
                200,
                json={
                    "screenshot_png": "iVBORw0KGgo=",
                    "screen_size": [1280, 720],
                    "windows": [],
                    "active_window_id": None,
                    "active_window_class": None,
                    "focused_app": "other",
                },
            )
        return httpx.Response(200, json={"ok": True})

    with DesktopClient(FakeSandbox(), transport=httpx.MockTransport(handler)) as client:
        assert client.screenshot() == b"\x89PNG\r\n\x1a\n"
        assert client.screen_size() == (1280, 720)
        assert client.cursor_position() == (2, 3)
        assert client.active_window().focused_app == "browser"
        assert client.observation().screen_size == (1280, 720)
        assert client.execute(MouseMoveAction(action="mouse_move", x=10, y=20)).ok
        client.click(10, 20)
        client.type_text("hello")
        client.key("ctrl+a")

    assert all(request.headers["authorization"] == "Bearer secret" for request in seen)


def test_client_raises_typed_error_for_http_failure() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(401, text="bad token"))

    with DesktopClient(FakeSandbox(), transport=transport) as client:
        with pytest.raises(DesktopRequestError, match="401"):
            client.screenshot()


def test_client_rejects_non_png_screenshot() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, content=b""))

    with DesktopClient(FakeSandbox(), transport=transport) as client:
        with pytest.raises(DesktopRequestError, match="not a PNG"):
            client.screenshot()


def test_client_timeout_is_a_typed_subclass_of_connection_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # noqa: ANN001
        raise httpx.TimeoutException("timed out")

    with DesktopClient(FakeSandbox(), transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(DesktopTimeoutError, match="timed out") as exc_info:
            client.screenshot()

    assert isinstance(exc_info.value, DesktopConnectionError)


def test_client_connection_error_is_not_a_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # noqa: ANN001
        raise httpx.ConnectError("could not connect")

    with DesktopClient(FakeSandbox(), transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(DesktopConnectionError) as exc_info:
            client.screenshot()

    assert not isinstance(exc_info.value, DesktopTimeoutError)
