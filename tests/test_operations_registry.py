from pathlib import Path

import pytest
from pydantic import ValidationError

from friday.operations.registry import OPERATIONS, parse_operation


def test_registry_covers_requested_operations() -> None:
    assert set(OPERATIONS) == {
        "launch_app",
        "open_url",
        "open_terminal_in",
        "open_file_manager",
        "open_file",
        "launch_browser_debug",
        "list_windows",
        "active_window",
        "focus_window",
        "close_window",
        "minimize_window",
        "maximize_window",
        "move_resize_window",
        "wait_for_window",
        "set_clipboard",
        "get_clipboard",
        "is_running",
        "list_processes",
        "close_app",
        "read_file",
        "write_file",
        "list_dir",
        "make_dir",
        "delete_file",
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"operation": "open_url", "url": "file:///tmp/a"},
        {"operation": "focus_window", "window_id": "123"},
        {"operation": "launch_app", "app": "sh"},
        {"operation": "open_file", "path": "../escape"},
    ],
)
def test_registry_rejects_unsafe_parameters(payload: dict[str, object]) -> None:
    with pytest.raises((ValidationError, ValueError)):
        parse_operation(payload, Path("/tmp/workspace"))
