"""Executor that dispatches typed actions and system operations through the control API."""

from __future__ import annotations

from typing import Protocol

from friday.actions.config import timeout_for
from friday.actions.models import Action, ActionResult, ZoomAction
from friday.desktop.client import DesktopClient
from friday.operations.registry import SystemOperation

from .zoom import zoom_image

Payload = Action | SystemOperation


class Executor(Protocol):
    def execute(self, payload: Payload) -> ActionResult | dict: ...


class RemoteExecutor:
    def __init__(self, client: DesktopClient) -> None:
        self._client = client

    def execute(self, payload: Payload) -> ActionResult | dict:
        if isinstance(payload, ZoomAction):
            view = zoom_image(self._client.screenshot(), payload.factor, payload.x, payload.y)
            return ActionResult(ok=True, image_png=view.image_png, zoom=view)
        operation = getattr(payload, "operation", None)
        if operation is not None:
            return self._client.operation(payload)
        return self._client.execute(payload, timeout=timeout_for(payload))
