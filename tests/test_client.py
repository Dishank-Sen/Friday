from __future__ import annotations

import httpx
import pytest

from friday.desktop.client import DesktopClient
from friday.desktop.errors import DesktopRequestError
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
            return httpx.Response(200, content=b"png")
        if request.url.path == "/screen_size":
            return httpx.Response(200, json={"width": 1280, "height": 720})
        return httpx.Response(200, json={"ok": True})

    with DesktopClient(FakeSandbox(), transport=httpx.MockTransport(handler)) as client:
        assert client.screenshot() == b"png"
        assert client.screen_size() == (1280, 720)
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
