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


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"operation": "launch_app", "app": "terminal"}, ["xfce4-terminal"]),
        (
            {"operation": "open_terminal_in", "path": "work"},
            ["xfce4-terminal", "--working-directory", "/tmp/workspace/work"],
        ),
        ({"operation": "open_file_manager", "path": "work"}, ["thunar", "/tmp/workspace/work"]),
        (
            {"operation": "open_file", "path": "work/a.txt"},
            ["xdg-open", "/tmp/workspace/work/a.txt"],
        ),
        (
            {"operation": "launch_browser_debug", "url": "https://example.com"},
            [
                "chromium",
                "--remote-debugging-port=9222",
                "--user-data-dir=/tmp/friday-chromium-debug",
                "https://example.com",
            ],
        ),
        ({"operation": "list_windows"}, ["wmctrl", "-lpG"]),
        ({"operation": "active_window"}, ["xdotool", "getactivewindow", "getwindowname"]),
        ({"operation": "close_window", "window_id": "0x1"}, ["wmctrl", "-i", "-c", "0x1"]),
        (
            {"operation": "minimize_window", "window_id": "0x1"},
            ["xdotool", "windowminimize", "0x1"],
        ),
        (
            {"operation": "maximize_window", "window_id": "0x1"},
            ["wmctrl", "-i", "-r", "0x1", "-b", "add,maximized_vert,maximized_horz"],
        ),
        (
            {"operation": "wait_for_window", "title": "Friday"},
            ["xdotool", "search", "--sync", "--onlyvisible", "--name", "Friday"],
        ),
        ({"operation": "get_clipboard"}, ["xclip", "-selection", "clipboard", "-o"]),
        ({"operation": "is_running", "name": "chromium"}, ["pgrep", "-x", "chromium"]),
        ({"operation": "list_processes"}, ["ps", "-eo", "pid,comm"]),
    ],
)
def test_all_subprocess_operation_argv(payload: dict[str, object], expected: list[str]) -> None:
    workspace = Path("/tmp/workspace")
    assert command_for_operation(parse_operation(payload, workspace), workspace) == expected
