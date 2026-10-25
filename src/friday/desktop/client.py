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
from friday.browser.models import BrowserState, ProbeStatus, WaitReady
from friday.desktop.observation import ActiveWindow, Observation
from friday.operations.registry import SystemOperation
from friday.sandbox.base import Sandbox

from .errors import DesktopConnectionError, DesktopRequestError, DesktopTimeoutError


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

    def observation(self) -> Observation:
        return self._model("GET", "/observation", Observation)

    def active_window(self) -> ActiveWindow:
        return self._model("GET", "/active_window", ActiveWindow)

    def execute(
        self, action: Action, timeout: float | None = None
    ) -> ActionResult:
        response = self._request(
            "POST", "/action", json=action.model_dump(mode="json"), timeout=timeout
        )
        try:
            return ActionResult.model_validate(response.json())
        except (TypeError, ValueError) as error:
            raise DesktopRequestError(502, "invalid action response") from error

    def operation(self, operation: SystemOperation) -> dict[str, object]:
        response = self._request("POST", "/operation", json=operation.model_dump(mode="json"))
        try:
            return response.json()
        except ValueError as error:
            raise DesktopRequestError(502, "invalid operation response") from error

    def browser_state(self) -> BrowserState:
        return self._model("GET", "/browser/state", BrowserState)

    def browser_wait_ready(self, timeout_s: float) -> WaitReady:
        if timeout_s <= 0:
            raise ValueError("timeout_s must be positive")
        response = self._request("POST", "/browser/wait_ready", json={"timeout_s": timeout_s})
        try:
            return WaitReady.model_validate(response.json())
        except (TypeError, ValueError) as error:
            raise DesktopRequestError(502, "invalid wait_ready response") from error

    def browser_status(self) -> ProbeStatus:
        return self._model("GET", "/browser/available", ProbeStatus)

    def click(self, x: int, y: int, button: int = 1) -> None:
        if button != 1:
            raise ValueError("only left click is supported by this compatibility method")
        self.execute(LeftClickAction(action="left_click", x=x, y=y))

    def type_text(self, text: str) -> None:
        self.execute(TypeAction(action="type", text=text))

    def key(self, combo: str) -> None:
        self.execute(KeyAction(action="key", key=combo))

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        timeout = kwargs.pop("timeout", None)
        request_kwargs: dict[str, Any] = kwargs
        if timeout is not None:
            request_kwargs["timeout"] = timeout
        try:
            response = self._client.request(method, path, **request_kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as error:
            detail = error.response.text
            raise DesktopRequestError(error.response.status_code, detail) from error
        except httpx.TimeoutException as error:
            raise DesktopTimeoutError(str(error)) from error
        except httpx.RequestError as error:
            raise DesktopConnectionError(str(error)) from error

    def _model(self, method: str, path: str, model: type[Any]) -> Any:
        try:
            return model.model_validate(self._request(method, path).json())
        except (TypeError, ValueError) as error:
            raise DesktopRequestError(502, f"invalid {path} response") from error
