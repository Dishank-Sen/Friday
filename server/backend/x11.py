from __future__ import annotations

import logging
import os
import tempfile
import threading
import time
from pathlib import Path

from friday.actions.config import MAX_DRAG_STEPS, timeout_for
from friday.actions.keys import normalize_key
from friday.actions.models import (
    Action,
    ActionResult,
    CursorPositionAction,
    HoldKeyAction,
    LeftClickDragAction,
    MouseMoveAction,
    ScreenshotAction,
    ShortcutAction,
    WaitAction,
    ZoomAction,
)
from friday.desktop.observation import (
    ActiveWindow,
    Observation,
    capture_observation,
    parse_active_window,
)
from friday.operations.registry import SystemOperation
from friday.shortcuts.registry import ShortcutNotAvailable, resolve_shortcut

from .base import BackendError
from .commands import (
    commands_for_action,
    key_command,
    key_down_command,
    key_up_command,
    mouse_down_command,
    mouse_up_command,
    move_command,
)
from .runner import CommandRunner
from .system import SystemBackend

LOGGER = logging.getLogger(__name__)


class X11Backend:
    def __init__(
        self, runner: CommandRunner, workspace: Path = Path("/config/friday-workspace")
    ) -> None:
        self._runner = runner
        self._lock = threading.RLock()
        self._held_buttons: set[int] = set()
        self._held_keys: set[str] = set()
        self._system = SystemBackend(runner, workspace)
        self.release_all()

    def execute_operation(self, operation: SystemOperation) -> dict[str, object]:
        with self._lock:
            return self._system.execute(operation)

    @property
    def workspace(self) -> Path:
        return self._system.workspace

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

    def observation(self) -> Observation:
        """Capture all display observation inputs while holding the display lock."""
        with self._lock:
            screenshot = self.screenshot()
            screen_size = self._runner.run(["xdotool", "getdisplaygeometry"])
            capture_error = None
            try:
                windows = self._runner.run(["wmctrl", "-lpGx"])
                active = self._runner.run(["xdotool", "getactivewindow"])
            except BackendError as error:
                LOGGER.warning("window observation failed", exc_info=True)
                windows, active = "", ""
                capture_error = str(error)
            try:
                return capture_observation(
                    screenshot, screen_size, windows, active, capture_error=capture_error
                )
            except ValueError as error:
                raise BackendError(str(error)) from error

    def active_window(self) -> ActiveWindow:
        """Read the focused X11 window under the display lock."""
        with self._lock:
            try:
                windows = self._runner.run(["wmctrl", "-lpGx"])
                active = self._runner.run(["xdotool", "getactivewindow"])
            except BackendError:
                LOGGER.warning("active window lookup failed", exc_info=True)
                return ActiveWindow(id=None, class_name=None, focused_app="other")
            return parse_active_window(windows, active)

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
        if isinstance(action, ShortcutAction):
            focused_app = self.active_window().focused_app
            try:
                keys = resolve_shortcut(action.name, focused_app)
            except ShortcutNotAvailable as error:
                return ActionResult(ok=False, detail=str(error))
            for _ in range(action.repeat):
                for key in keys:
                    self._runner.run(key_command(key))
            return ActionResult(ok=True)
        self._validate_action_bounds(action)
        budget = timeout_for(action)
        for command in commands_for_action(action):
            self._runner.run(command, timeout=budget)
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
