"""HTTP client for the desktop control server."""

from __future__ import annotations

from typing import Any

import httpx

from friday.actions.models import (
    Action,
    ActionResult,
    KeyAction,
    LeftClickAction,
    TypeAction,
)
from friday.sandbox.base import Sandbox

from .errors import DesktopConnectionError, DesktopRequestError


class DesktopClient:
    def __init__(
        self,
        sandbox: Sandbox,
        timeout: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self._sandbox = sandbox
        self._client = httpx.Client(
            base_url=sandbox.api_url,
            headers={"Authorization": f"Bearer {sandbox.token}"},
            timeout=timeout,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> DesktopClient:
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()

    def screenshot(self) -> bytes:
        content = self._request("GET", "/screenshot").content
        if not content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise DesktopRequestError(502, "screenshot response was not a PNG image")
        return content

    def screen_size(self) -> tuple[int, int]:
        data = self._request("GET", "/screen_size").json()
        try:
            return int(data["width"]), int(data["height"])
        except (KeyError, TypeError, ValueError) as error:
            raise DesktopRequestError(502, "invalid screen size response") from error

    def cursor_position(self) -> tuple[int, int]:
        data = self._request("GET", "/cursor").json()
        try:
            return int(data["x"]), int(data["y"])
        except (KeyError, TypeError, ValueError) as error:
            raise DesktopRequestError(502, "invalid cursor response") from error

    def execute(self, action: Action) -> ActionResult:
        response = self._request("POST", "/action", json=action.model_dump(mode="json"))
        try:
            return ActionResult.model_validate(response.json())
        except (TypeError, ValueError) as error:
            raise DesktopRequestError(502, "invalid action response") from error

    def click(self, x: int, y: int, button: int = 1) -> None:
        if button != 1:
            raise ValueError("only left click is supported by this compatibility method")
        self.execute(LeftClickAction(action="left_click", x=x, y=y))

    def type_text(self, text: str) -> None:
        self.execute(TypeAction(action="type", text=text))

    def key(self, combo: str) -> None:
        self.execute(KeyAction(action="key", key=combo))

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = self._client.request(method, path, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as error:
            detail = error.response.text
            raise DesktopRequestError(error.response.status_code, detail) from error
        except httpx.RequestError as error:
            raise DesktopConnectionError(str(error)) from error
