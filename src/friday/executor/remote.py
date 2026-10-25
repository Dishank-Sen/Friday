"""Executor that dispatches typed actions through the control API."""

from __future__ import annotations

from typing import Protocol

from friday.actions.config import timeout_for
from friday.actions.models import Action, ActionResult, ZoomAction
from friday.desktop.client import DesktopClient

from .zoom import zoom_image


class Executor(Protocol):
    def execute(self, action: Action) -> ActionResult: ...


class RemoteExecutor:
    def __init__(self, client: DesktopClient) -> None:
        self._client = client

    def execute(self, action: Action) -> ActionResult:
        if isinstance(action, ZoomAction):
            view = zoom_image(self._client.screenshot(), action.factor, action.x, action.y)
            return ActionResult(ok=True, image_png=view.image_png, zoom=view)
        return self._client.execute(action, timeout=timeout_for(action))
