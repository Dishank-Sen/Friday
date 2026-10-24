from __future__ import annotations

import logging
import os
import tempfile
import threading
import time
from pathlib import Path

from friday.actions.config import MAX_DRAG_STEPS
from friday.actions.keys import normalize_key
from friday.actions.models import (
    Action,
    ActionResult,
    CursorPositionAction,
    HoldKeyAction,
    LeftClickDragAction,
    MouseMoveAction,
    ScreenshotAction,
    WaitAction,
    ZoomAction,
)

from .base import BackendError
from .commands import (
    commands_for_action,
    key_down_command,
    key_up_command,
    mouse_down_command,
    mouse_up_command,
    move_command,
)
from .runner import CommandRunner

LOGGER = logging.getLogger(__name__)


class X11Backend:
    def __init__(self, runner: CommandRunner) -> None:
        self._runner = runner
        self._lock = threading.RLock()
        self._held_buttons: set[int] = set()
        self._held_keys: set[str] = set()
        self.release_all()

    def execute(self, action: Action) -> ActionResult:
        started = time.monotonic()
        with self._lock:
            try:
                result = self._execute_locked(action)
            except BaseException:
                self.release_all()
                LOGGER.info(
                    "desktop action failed: action=%s duration_seconds=%.3f",
                    action.action,
                    time.monotonic() - started,
                )
                raise
        LOGGER.info(
            "desktop action succeeded: action=%s duration_seconds=%.3f",
            action.action,
            time.monotonic() - started,
        )
        return result

    def screenshot(self) -> bytes:
        with self._lock:
            descriptor, image_name = tempfile.mkstemp(suffix=".png")
            os.close(descriptor)
            Path(image_name).unlink(missing_ok=True)
            try:
                self._runner.run(["scrot", "--", image_name])
                image = Path(image_name).read_bytes()
            except FileNotFoundError as error:
                raise BackendError("scrot did not create a screenshot") from error
            finally:
                Path(image_name).unlink(missing_ok=True)
            if not image.startswith(b"\x89PNG\r\n\x1a\n"):
                raise BackendError("scrot did not produce a PNG image")
            return image

    def screen_size(self) -> tuple[int, int]:
        output = self._runner.run(["xdotool", "getdisplaygeometry"]).strip().split()
        if len(output) != 2:
            raise BackendError("xdotool returned invalid display geometry")
        try:
            return int(output[0]), int(output[1])
        except ValueError as error:
            raise BackendError("xdotool returned invalid display geometry") from error

    def cursor_position(self) -> tuple[int, int]:
        output = self._runner.run(["xdotool", "getmouselocation", "--shell"])
        values = dict(line.split("=", 1) for line in output.splitlines() if "=" in line)
        try:
            return int(values["X"]), int(values["Y"])
        except (KeyError, ValueError) as error:
            raise BackendError("xdotool returned invalid cursor position") from error

    def release_all(self) -> None:
        with self._lock:
            for key in list(self._held_keys):
                try:
                    self._runner.run(key_up_command(key))
                except BackendError:
                    LOGGER.warning("could not release held key", exc_info=True)
                finally:
                    self._held_keys.discard(key)
            for button in list(self._held_buttons):
                try:
                    self._runner.run(mouse_up_command(button))
                except BackendError:
                    LOGGER.warning("could not release held mouse button", exc_info=True)
                finally:
                    self._held_buttons.discard(button)

    def _execute_locked(self, action: Action) -> ActionResult:
        if isinstance(action, ScreenshotAction):
            return ActionResult(ok=True, image_png=self.screenshot())
        if isinstance(action, CursorPositionAction):
            return ActionResult(ok=True, point=self.cursor_position())
        if isinstance(action, ZoomAction):
            raise BackendError("zoom is a host-only action")
        if isinstance(action, WaitAction):
            time.sleep(action.seconds)
            return ActionResult(ok=True)
        if isinstance(action, MouseMoveAction):
            self._validate_point(action.x, action.y)
            self._move(action.x, action.y, action.duration)
            return ActionResult(ok=True)
        if isinstance(action, LeftClickDragAction):
            self._validate_point(action.start_x, action.start_y)
            self._validate_point(action.end_x, action.end_y)
            self._drag(action)
            return ActionResult(ok=True)
        if isinstance(action, HoldKeyAction):
            self._hold_key(action)
            return ActionResult(ok=True)
        self._validate_action_bounds(action)
        for command in commands_for_action(action):
            self._runner.run(command)
        self._track_mouse_button(action)
        return ActionResult(ok=True)

    def _validate_action_bounds(self, action: Action) -> None:
        for x_name, y_name in (("x", "y"),):
            x = getattr(action, x_name, None)
            y = getattr(action, y_name, None)
            if x is not None or y is not None:
                self._validate_point(x, y)

    def _validate_point(self, x: int | None, y: int | None) -> None:
        if x is None or y is None:
            raise BackendError("both x and y coordinates are required")
        width, height = self.screen_size()
        if not 0 <= x < width or not 0 <= y < height:
            raise BackendError(f"coordinates ({x}, {y}) are outside display {width}x{height}")

    def _move(self, end_x: int, end_y: int, duration: float) -> None:
        if duration == 0:
            self._runner.run(move_command(end_x, end_y))
            return
        start_x, start_y = self.cursor_position()
        steps = MAX_DRAG_STEPS
        for step in range(1, steps + 1):
            fraction = step / steps
            x = round(start_x + (end_x - start_x) * fraction)
            y = round(start_y + (end_y - start_y) * fraction)
            self._runner.run(move_command(x, y))
            time.sleep(duration / steps)

    def _drag(self, action: LeftClickDragAction) -> None:
        self._runner.run(move_command(action.start_x, action.start_y))
        self._runner.run(mouse_down_command())
        self._held_buttons.add(1)
        try:
            for step in range(1, MAX_DRAG_STEPS + 1):
                fraction = step / MAX_DRAG_STEPS
                x = round(action.start_x + (action.end_x - action.start_x) * fraction)
                y = round(action.start_y + (action.end_y - action.start_y) * fraction)
                self._runner.run(move_command(x, y))
                time.sleep(0.03)
        finally:
            self._runner.run(mouse_up_command())
            self._held_buttons.discard(1)

    def _hold_key(self, action: HoldKeyAction) -> None:
        key = normalize_key(action.key)
        self._runner.run(key_down_command(key))
        self._held_keys.add(key)
        try:
            time.sleep(action.duration)
        finally:
            self._runner.run(key_up_command(key))
            self._held_keys.discard(key)

    def _track_mouse_button(self, action: Action) -> None:
        if action.action == "left_mouse_down":
            self._held_buttons.add(1)
        elif action.action == "left_mouse_up":
            self._held_buttons.discard(1)
