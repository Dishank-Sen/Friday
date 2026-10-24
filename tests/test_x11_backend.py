from __future__ import annotations

import threading
import time

import pytest

from friday.actions.models import (
    HoldKeyAction,
    LeftClickAction,
    LeftMouseDownAction,
    MouseMoveAction,
)
from server.backend.base import BackendError
from server.backend.x11 import X11Backend


class FakeRunner:
    def __init__(self, fail_on: str | None = None, pause: bool = True) -> None:
        self.commands: list[list[str]] = []
        self.fail_on = fail_on
        self.pause = pause
        self.active = 0
        self.max_active = 0
        self._lock = threading.Lock()

    def run(self, argv: list[str]) -> str:
        with self._lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            self.commands.append(argv)
            if self.fail_on and self.fail_on in argv:
                raise BackendError("runner failed")
            if argv == ["xdotool", "getdisplaygeometry"]:
                return "100 80\n"
            if argv == ["xdotool", "getmouselocation", "--shell"]:
                return "X=0\nY=0\n"
            if self.pause:
                time.sleep(0.005)
            return ""
        finally:
            with self._lock:
                self.active -= 1


def test_backend_rejects_out_of_bounds_coordinates() -> None:
    backend = X11Backend(FakeRunner())

    with pytest.raises(BackendError, match="outside display"):
        backend.execute(LeftClickAction(action="left_click", x=100, y=0))


def test_backend_serializes_actions() -> None:
    runner = FakeRunner()
    backend = X11Backend(runner)
    actions = [MouseMoveAction(action="mouse_move", x=1, y=1) for _ in range(2)]
    threads = [threading.Thread(target=backend.execute, args=(action,)) for action in actions]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert runner.max_active == 1


def test_backend_releases_held_mouse_after_failure() -> None:
    runner = FakeRunner(fail_on="click")
    backend = X11Backend(runner)
    backend.execute(LeftMouseDownAction(action="left_mouse_down"))

    with pytest.raises(BackendError):
        backend.execute(LeftClickAction(action="left_click", x=1, y=1))

    assert ["xdotool", "mouseup", "1"] in runner.commands


def test_hold_key_releases_on_interrupted_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = FakeRunner(pause=False)
    backend = X11Backend(runner)

    def interrupted(_: float) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr("server.backend.x11.time.sleep", interrupted)
    with pytest.raises(KeyboardInterrupt):
        backend.execute(HoldKeyAction(action="hold_key", key="shift", duration=1))

    assert ["xdotool", "keyup", "--", "shift"] in runner.commands
