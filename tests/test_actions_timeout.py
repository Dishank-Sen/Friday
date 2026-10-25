"""Per-action execution timeouts: a slow action is not killed early."""

from __future__ import annotations

from friday.actions.config import DEFAULT_EXECUTION_TIMEOUT, timeout_for
from friday.actions.models import (
    HoldKeyAction,
    LeftClickAction,
    MouseMoveAction,
    TypeAction,
    WaitAction,
)
from friday.operations.registry import WaitForWindow


def test_plain_click_uses_the_default_timeout() -> None:
    assert timeout_for(LeftClickAction(action="left_click", x=10, y=10)) == (
        DEFAULT_EXECUTION_TIMEOUT
    )


def test_max_duration_wait_is_not_killed_early() -> None:
    # maximum allowed wait is MAX_WAIT_SECONDS (10s); the timeout must exceed it
    assert timeout_for(WaitAction(action="wait", seconds=10.0)) > 10.0


def test_max_hold_and_slow_move_are_not_killed_early() -> None:
    assert timeout_for(HoldKeyAction(action="hold_key", key="ctrl", duration=5.0)) > 5.0
    assert timeout_for(MouseMoveAction(action="mouse_move", x=5, y=5, duration=2.0)) > 2.0


def test_long_type_is_not_killed_early() -> None:
    # 500 chars at ~20ms each is ~10s of typing; the timeout must exceed it
    assert timeout_for(TypeAction(action="type", text="x" * 500)) > 10.0


def test_wait_for_window_operation_adds_margin() -> None:
    op = WaitForWindow(operation="wait_for_window", title="term", timeout=5.0)
    assert timeout_for(op) > 5.0