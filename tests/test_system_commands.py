from pathlib import Path

import pytest

from friday.operations.registry import parse_operation
from server.backend.commands import command_for_operation


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (
            {"operation": "open_url", "url": "https://example.com/a b"},
            ["chromium", "https://example.com/a b"],
        ),
        (
            {"operation": "focus_window", "window_id": "0x1a"},
            ["wmctrl", "-i", "-a", "0x1a"],
        ),
        (
            {"operation": "set_clipboard", "text": "-text"},
            ["xclip", "-selection", "clipboard", "-loops", "0"],
        ),
        (
            {
                "operation": "move_resize_window",
                "window_id": "0x1a",
                "x": 1,
                "y": 2,
                "width": 3,
                "height": 4,
            },
            ["wmctrl", "-i", "-r", "0x1a", "-e", "0,1,2,3,4"],
        ),
    ],
)
def test_system_operation_argv(payload: dict[str, object], expected: list[str]) -> None:
    workspace = Path("/tmp/workspace")
    operation = parse_operation(payload, workspace)
    assert command_for_operation(operation, workspace) == expected
