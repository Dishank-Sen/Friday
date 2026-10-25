"""Shortcut execution resolves against a fresh focus read, not state."""

from __future__ import annotations

from pathlib import Path

from friday.actions.models import parse_action
from friday.desktop.observation import parse_active_window
from server.backend.x11 import X11Backend

FIXTURES = Path(__file__).parent / "fixtures" / "observation"


class _FakeRunner:
    """Runs the fixture's X11 commands; the active window is the terminal.

    ``active_window.txt`` (decimal 50331650 -> 0x03000002) points at the
    chromium window in the fixture, but a live backend reads fresh focus: we
    override it to the terminal window (0x01600003) so copy -> ctrl+shift+c.
    """

    TERMINAL_ID = "0x01600003"

    def __init__(self) -> None:
        self.commands: list[list[str]] = []
        self.active_hex = self.TERMINAL_ID

    def run(self, argv: list[str], *, timeout: float = 10.0) -> str:
        self.commands.append(argv)
        if argv == ["wmctrl", "-lpGx"]:
            return (FIXTURES / "wmctrl_lpgx.txt").read_text(encoding="utf-8")
        if argv == ["xdotool", "getactivewindow"]:
            return str(int(self.active_hex, 16))  # decimal form the backend expects
        if argv == ["xdotool", "getdisplaygeometry"]:
            return "1280 720\n"
        if argv == ["xdotool", "getmouselocation", "--shell"]:
            return "X=0\nY=0\n"
        return ""

    def start(self, argv: list[str]):  # noqa: ANN201
        return None

    def start_with_stdin(self, argv: list[str], stdin: str):  # noqa: ANN001, ANN201
        return None


def test_fresh_focus_read_beats_state_focused_app() -> None:
    """State says browser, but the fresh active-window read is the terminal."""
    runner = _FakeRunner()
    backend = X11Backend(runner)

    # xdotool getactivewindow returns the terminal window, so resolve "copy"
    backend.execute(parse_action('{"action":"shortcut","name":"copy"}'))

    # the terminal binding of copy is ctrl+shift+c, NOT the default ctrl+c
    assert ["xdotool", "key", "--", "ctrl+shift+c"] in runner.commands


def test_fresh_focus_read_uses_terminal_binding() -> None:
    runner = _FakeRunner()
    active = parse_active_window(
        (FIXTURES / "wmctrl_lpgx.txt").read_text(encoding="utf-8"),
        str(int(runner.TERMINAL_ID, 16)),
    )
    assert active.focused_app == "terminal"