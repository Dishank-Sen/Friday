import pytest
from pydantic import ValidationError

from friday.actions.keys import normalize_key
from friday.actions.models import ACTION_ADAPTER, ShortcutAction
from friday.shortcuts.registry import SHORTCUTS, normalized_keys
from server.backend.commands import commands_for_action


def test_shortcut_registry_is_unique_and_normalizes_all_keys() -> None:
    assert len(SHORTCUTS) == len(set(SHORTCUTS))
    assert {entry.context for entry in SHORTCUTS.values()} == {
        "text",
        "browser",
        "form",
        "window",
        "terminal",
        "file_manager",
    }
    for entry in SHORTCUTS.values():
        assert entry.requires_focus
        assert entry.expected_effect
        assert normalized_keys(entry) == tuple(normalize_key(key) for key in entry.keys)


def test_shortcut_action_expands_repeat_through_existing_key_command() -> None:
    action = ShortcutAction(action="shortcut", name="browser_new_tab", repeat=2)

    assert commands_for_action(action) == [
        ["xdotool", "key", "--", "ctrl+t"],
        ["xdotool", "key", "--", "ctrl+t"],
    ]


@pytest.mark.parametrize("repeat", [0, 11])
def test_shortcut_repeat_is_limited(repeat: int) -> None:
    with pytest.raises(ValidationError):
        ShortcutAction(action="shortcut", name="browser_new_tab", repeat=repeat)


def test_unknown_shortcut_lists_close_matches() -> None:
    with pytest.raises(ValidationError, match="browser_new_tab"):
        ACTION_ADAPTER.validate_python({"action": "shortcut", "name": "browser_new_tba"})


def test_risky_shortcuts_are_marked() -> None:
    assert SHORTCUTS["window_close"].risky
    assert SHORTCUTS["file_delete_to_trash"].risky
    assert SHORTCUTS["terminal_interrupt"].risky
