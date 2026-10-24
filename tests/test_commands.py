from friday.actions.models import (
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
from server.backend.commands import commands_for_action


def test_click_commands() -> None:
    assert commands_for_action(LeftClickAction(action="left_click", x=2, y=3)) == [
        ["xdotool", "mousemove", "2", "3"],
        ["xdotool", "click", "1"],
    ]
    assert commands_for_action(RightClickAction(action="right_click", x=2, y=3))[-1] == [
        "xdotool",
        "click",
        "3",
    ]
    assert commands_for_action(MiddleClickAction(action="middle_click", x=2, y=3))[-1] == [
        "xdotool",
        "click",
        "2",
    ]
    assert commands_for_action(DoubleClickAction(action="double_click", x=2, y=3))[-1] == [
        "xdotool",
        "click",
        "--repeat",
        "2",
        "--delay",
        "100",
        "1",
    ]
    assert commands_for_action(TripleClickAction(action="triple_click", x=2, y=3))[-1][3] == "3"


def test_type_newlines_and_key_commands() -> None:
    assert commands_for_action(TypeAction(action="type", text="one\ntwo")) == [
        ["xdotool", "type", "--delay", "20", "--", "one"],
        ["xdotool", "key", "--", "Return"],
        ["xdotool", "type", "--delay", "20", "--", "two"],
    ]
    assert commands_for_action(KeyAction(action="key", key="control+enter")) == [
        ["xdotool", "key", "--", "ctrl+Return"]
    ]


def test_scroll_and_mouse_button_commands() -> None:
    assert commands_for_action(ScrollAction(action="scroll", amount=2)) == [
        ["xdotool", "click", "5"],
        ["xdotool", "click", "5"],
    ]
    assert commands_for_action(ScrollAction(action="scroll", amount=-1, horizontal=True)) == [
        ["xdotool", "click", "6"]
    ]
    assert commands_for_action(LeftMouseDownAction(action="left_mouse_down")) == [
        ["xdotool", "mousedown", "1"]
    ]
    assert commands_for_action(LeftMouseUpAction(action="left_mouse_up")) == [
        ["xdotool", "mouseup", "1"]
    ]
