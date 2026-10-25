"""Pure screenshot-diff and step-outcome computation for the verify node.

This module is deliberately free of I/O: compare() takes image file paths and
returns an objective DiffResult, and step_outcome() turns that plus the action's
screen-change expectation into the step's outcome label. Every function here is
pure and deterministic, so the tricky screen-diffing logic is fully unit-
testable without a desktop or container.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops

from .verify_settings import DiffSettings

# Steps whose operation is expected to change what is on screen. An operation
# in this set that produces little/no visible change is judged
# ``no_visible_change`` (a stalled step); one not in this set that did not
# change is ``no_change_expected`` (normal). Defaults are a starting point and
# must be tuned on the real container.
EXPECTS_SCREEN_CHANGE: frozenset[str] = frozenset(
    {
        "left_click",
        "right_click",
        "middle_click",
        "double_click",
        "triple_click",
        "left_click_drag",
        "scroll",
        "type",
        "key",
        "shortcut",
        "open_url",
        "launch_app",
        "focus_window",
        "close_window",
        "minimize_window",
        "maximize_window",
        "move_resize_window",
        "open_terminal_in",
        "open_file_manager",
        "open_file",
        "launch_browser_debug",
        "write_file",
        "delete_file",
        "make_dir",
        "set_clipboard",
    }
)

# Operations explicitly NOT expected to change the screen: waits, pure cursor
# moves, held input, and read-only / observation operations.
_NO_EXPECTED_CHANGE: frozenset[str] = frozenset(
    {
        "wait",
        "mouse_move",
        "hold_key",
        "screenshot",
        "cursor_position",
        "screen_size",
        "zoom",
        "list_windows",
        "active_window",
        "get_clipboard",
        "read_file",
        "list_dir",
        "is_running",
        "list_processes",
        "wait_for_window",
    }
)


class ScreenshotUnavailableError(Exception):
    """A screenshot path was missing or unreadable."""


@dataclass(frozen=True, slots=True)
class DiffResult:
    """Objective verdict about whether the pre/post screenshots differ."""

    label: str  # "changed" | "unchanged" | "size_changed" | "unreliable"
    changed_ratio: float | None  # fraction of changed pixels, None if unreliable

    @property
    def count_as_changed(self) -> bool:
        return self.label in {"changed", "size_changed"}


def _load(path: str | Path) -> Image.Image:
    try:
        return Image.open(path).convert("RGB")
    except (OSError, ValueError) as error:
        raise ScreenshotUnavailableError(str(path)) from error


def _diff_ratio(before: Image.Image, after: Image.Image, settings: DiffSettings) -> float:
    """Fraction of pixels whose per-channel difference exceeds the tolerance.

    ``ignore_regions`` are excluded before counting so self-changing regions
    (the panel clock, the cursor blink) do not count as a real change.
    """
    before = before.convert("RGB")
    after = after.convert("RGB")
    diff = ImageChops.difference(before, after)
    grayscale = diff.convert("L")
    threshold = max(0, min(255, settings.tolerance))

    def is_changed(pixel: int) -> int:
        return 255 if pixel > threshold else 0

    changed_mask = grayscale.point(is_changed).convert("1")

    total = before.size[0] * before.size[1]
    if total == 0:
        return 0.0
    # histogram of a 1-bit image: index 0 is unchanged (black), 255 is changed (white)
    histogram = changed_mask.histogram()
    changed = histogram[255] if len(histogram) == 256 else 0
    for (rx, ry, rw, rh) in settings.ignore_regions:
        region = changed_mask.crop((rx, ry, rx + rw, ry + rh))
        h = region.histogram()
        changed -= h[255] if len(h) == 256 else 0
    changed = max(0, changed)
    return changed / total


def compare(
    prev_path: str | Path,
    screenshot_path: str | Path,
    settings: DiffSettings,
) -> DiffResult:
    """Compare two screenshots and label the change.

    Returns ``unreliable`` (changed_ratio None) when either path is missing or
    unreadable (Pillow failure). Dimensions mismatching counts as a change and
    is flagged (``size_changed``).
    """
    try:
        before = _load(prev_path)
        after = _load(screenshot_path)
    except ScreenshotUnavailableError:
        return DiffResult(label="unreliable", changed_ratio=None)

    if before.size != after.size:
        return DiffResult(label="size_changed", changed_ratio=None)

    ratio = _diff_ratio(before, after, settings)
    label = "changed" if ratio >= settings.min_changed_ratio else "unchanged"
    return DiffResult(label=label, changed_ratio=round(ratio, 6))


# --- step outcome ------------------------------------------------------------


def expects_screen_change(operation: str) -> bool:
    """Whether an operation is expected to change the screen.

    The explicit no-change set (waits, cursor moves, held input, read-only and
    observation operations) is False; everything else defaults to True, so an
    operation we have not yet classified is optimistically treated as
    should-change (a missed classification would otherwise silently pass a
    stalled step).
    """
    return operation not in _NO_EXPECTED_CHANGE


def step_outcome(
    operation: str,
    ok: bool,
    diff: DiffResult,
) -> str:
    """The step's outcome label from the action result and the screenshot diff.

    One of ``failed`` / ``no_visible_change`` / ``changed`` /
    ``no_change_expected`` / ``unknown``.
    """
    if not ok:
        return "failed"
    if diff.label == "unreliable":
        return "unknown"
    expected = expects_screen_change(operation)
    if diff.count_as_changed:
        return "changed"
    if expected:
        return "no_visible_change"
    return "no_change_expected"