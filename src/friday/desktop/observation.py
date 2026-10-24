"""Typed, pure parsing for X11 observation command output."""

from __future__ import annotations

import base64
import re

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from friday.actions.focus import IGNORED_WINDOW_CLASSES, focused_app_for

_WINDOW_LINE = re.compile(
    r"^(?P<id>0x[0-9a-fA-F]+)\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+"
    r"(?P<class_name>.+?)\s{2,}\S+\s*(?P<title>.*)$"
)
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


class WindowInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    class_name: str
    active: bool


class ActiveWindow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None
    class_name: str | None
    focused_app: str


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    screenshot_png: bytes
    screen_size: tuple[int, int]
    windows: list[WindowInfo]
    active_window_id: str | None
    active_window_class: str | None
    focused_app: str

    @field_serializer("screenshot_png", when_used="json")
    def _serialize_screenshot(self, image: bytes) -> str:
        return base64.b64encode(image).decode("ascii")

    @field_validator("screenshot_png", mode="before")
    @classmethod
    def _deserialize_screenshot(cls, image: object) -> object:
        if isinstance(image, str):
            return base64.b64decode(image, validate=True)
        return image


def capture_observation(
    screenshot_png: bytes,
    screen_size_output: str,
    windows_output: str,
    active_window_output: str,
) -> Observation:
    """Parse a coherent X11 command snapshot into safe observation data."""
    screen_size = _screen_size(screen_size_output)
    active_window_id = decimal_window_id_to_hex(active_window_output)
    windows = parse_windows(windows_output, active_window_id)
    active = next((window for window in windows if window.active), None)
    return Observation(
        screenshot_png=screenshot_png,
        screen_size=screen_size,
        windows=windows,
        active_window_id=active_window_id,
        active_window_class=None if active is None else active.class_name,
        focused_app=focused_app_for(None if active is None else active.class_name),
    )


def parse_active_window(windows_output: str, active_window_output: str) -> ActiveWindow:
    """Parse fresh active-window metadata from the same window-list format."""
    active_window_id = decimal_window_id_to_hex(active_window_output)
    windows = parse_windows(windows_output, active_window_id)
    active = next((window for window in windows if window.active), None)
    return ActiveWindow(
        id=active_window_id,
        class_name=None if active is None else active.class_name,
        focused_app=focused_app_for(None if active is None else active.class_name),
    )


def parse_windows(output: str, active_window_id: str | None) -> list[WindowInfo]:
    """Parse, filter, sanitize, cap, and active-sort wmctrl -lpGx output."""
    windows: list[WindowInfo] = []
    for line in output.splitlines():
        match = _WINDOW_LINE.match(line)
        if match is None:
            continue
        window_id = normalize_hex_window_id(match.group("id"))
        class_name = match.group("class_name").strip()
        if _is_ignored(class_name):
            continue
        windows.append(
            WindowInfo(
                id=window_id,
                title=sanitize_title(match.group("title")),
                class_name=class_name,
                active=window_id == active_window_id,
            )
        )
    windows.sort(key=lambda window: not window.active)
    return windows[:15]


def decimal_window_id_to_hex(output: str) -> str | None:
    """Convert xdotool's decimal ID to the canonical eight-digit hex form."""
    value = output.strip()
    if not value:
        return None
    try:
        return f"0x{int(value):08x}"
    except ValueError:
        return None


def normalize_hex_window_id(value: str) -> str:
    """Normalize a wmctrl hex ID to the active-window comparison form."""
    return f"0x{int(value, 16):08x}"


def sanitize_title(title: str) -> str:
    """Remove control text, collapse whitespace, and bound untrusted titles."""
    return " ".join(_CONTROL.sub(" ", title).split())[:80]


def _screen_size(output: str) -> tuple[int, int]:
    parts = output.strip().split()
    if len(parts) != 2:
        raise ValueError("invalid display geometry")
    try:
        width, height = (int(part) for part in parts)
    except ValueError as error:
        raise ValueError("invalid display geometry") from error
    if width <= 0 or height <= 0:
        raise ValueError("invalid display geometry")
    return width, height


def _is_ignored(class_name: str) -> bool:
    normalized = class_name.lower()
    return any(normalized.startswith(ignored) for ignored in IGNORED_WINDOW_CLASSES)
