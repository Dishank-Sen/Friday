from __future__ import annotations

from pathlib import Path

from friday.actions.keys import normalize_key
from friday.actions.models import (
    Action,
    DoubleClickAction,
    KeyAction,
    LeftClickAction,
    LeftMouseDownAction,
    LeftMouseUpAction,
    MiddleClickAction,
    RightClickAction,
    ScrollAction,
    TripleClickAction,
    TypeAction,
)
from friday.operations.registry import SystemOperation, _argv


def move_command(x: int, y: int) -> list[str]:
    return ["xdotool", "mousemove", str(x), str(y)]


def click_command(button: int, count: int = 1) -> list[str]:
    if count == 1:
        return ["xdotool", "click", str(button)]
    return ["xdotool", "click", "--repeat", str(count), "--delay", "100", str(button)]


def mouse_down_command(button: int = 1) -> list[str]:
    return ["xdotool", "mousedown", str(button)]


def mouse_up_command(button: int = 1) -> list[str]:
    return ["xdotool", "mouseup", str(button)]


def key_command(key: str) -> list[str]:
    return ["xdotool", "key", "--", normalize_key(key)]


def key_down_command(key: str) -> list[str]:
    return ["xdotool", "keydown", "--", normalize_key(key)]


def key_up_command(key: str) -> list[str]:
    return ["xdotool", "keyup", "--", normalize_key(key)]


def type_commands(text: str) -> list[list[str]]:
    commands: list[list[str]] = []
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if line:
            commands.append(["xdotool", "type", "--delay", "20", "--", line])
        if index < len(lines) - 1:
            commands.append(["xdotool", "key", "--", "Return"])
    return commands


def scroll_commands(action: ScrollAction) -> list[list[str]]:
    if action.horizontal:
        button = 7 if action.amount > 0 else 6
    else:
        button = 5 if action.amount > 0 else 4
    return [click_command(button) for _ in range(abs(action.amount))]


def commands_for_action(action: Action) -> list[list[str]]:
    match action:
        case LeftClickAction(x=x, y=y):
            return [move_command(x, y), click_command(1)]
        case RightClickAction(x=x, y=y):
            return [move_command(x, y), click_command(3)]
        case MiddleClickAction(x=x, y=y):
            return [move_command(x, y), click_command(2)]
        case DoubleClickAction(x=x, y=y):
            return [move_command(x, y), click_command(1, 2)]
        case TripleClickAction(x=x, y=y):
            return [move_command(x, y), click_command(1, 3)]
        case LeftMouseDownAction():
            return [mouse_down_command()]
        case LeftMouseUpAction():
            return [mouse_up_command()]
        case TypeAction(text=text):
            return type_commands(text)
        case KeyAction(key=key):
            return [key_command(key)]
        case ScrollAction() as scroll:
            commands = [] if scroll.x is None else [move_command(scroll.x, scroll.y)]
            return commands + scroll_commands(scroll)
        case _:
            return []


def command_for_operation(operation: SystemOperation, workspace: Path) -> list[str] | None:
    """Return the fixed argv for a validated system operation."""
    return _argv(operation, workspace)
