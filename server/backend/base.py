from __future__ import annotations

from typing import Protocol

from friday.actions.models import Action, ActionResult
from friday.desktop.observation import ActiveWindow, Observation


class BackendError(RuntimeError):
    """An X11 command could not be completed."""


class DesktopBackend(Protocol):
    def execute(self, action: Action) -> ActionResult: ...

    def screenshot(self) -> bytes: ...

    def screen_size(self) -> tuple[int, int]: ...

    def cursor_position(self) -> tuple[int, int]: ...

    def observation(self) -> Observation: ...

    def active_window(self) -> ActiveWindow: ...

    def release_all(self) -> None: ...
