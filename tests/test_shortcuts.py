import pytest
from pydantic import ValidationError

from friday.actions.keys import normalize_key
from friday.actions.models import ACTION_ADAPTER, ShortcutAction
from friday.shortcuts.registry import ALIASES, SHORTCUTS, ShortcutNotAvailable, resolve_shortcut

FOCUSED_APPS = ("browser", "terminal", "file_manager", "text_editor", "other")


def test_shortcut_registry_has_unique_names_and_valid_bindings() -> None:
    assert len(SHORTCUTS) == len(set(SHORTCUTS))
    for entry in SHORTCUTS.values():
        assert entry.expected_effect
        for keys in entry.bindings.values():
            if keys is not None:
                assert all(normalize_key(key) for key in keys)


@pytest.mark.parametrize("name", SHORTCUTS)
@pytest.mark.parametrize("focused_app", FOCUSED_APPS)
def test_every_logical_shortcut_has_a_defined_focus_resolution(
    name: str, focused_app: str
) -> None:
    try:
        keys = resolve_shortcut(name, focused_app)
    except ShortcutNotAvailable as error:
        assert error.name == name
        assert error.focused_app == focused_app
        assert error.available_contexts
    else:
        assert keys


@pytest.mark.parametrize(
    "focused_app, expected",
    [("terminal", ["ctrl+shift+c"]), ("browser", ["ctrl+c"]), ("other", ["ctrl+c"])],
)
def test_copy_resolves_by_focused_app(focused_app: str, expected: list[str]) -> None:
    assert resolve_shortcut("copy", focused_app) == expected


def test_explicit_null_does_not_fall_back_to_default() -> None:
    with pytest.raises(ShortcutNotAvailable, match="undo is available in: default"):
        resolve_shortcut("undo", "terminal")


@pytest.mark.parametrize("name", ["terminal_interrupt", "browser_new_tab", "file_rename"])
def test_context_only_shortcuts_reject_other_apps(name: str) -> None:
    with pytest.raises(ShortcutNotAvailable) as error:
        resolve_shortcut(name, "other")
    assert error.value.available_contexts


@pytest.mark.parametrize("alias, canonical", ALIASES.items())
def test_deprecated_aliases_resolve(alias: str, canonical: str) -> None:
    focused_app = "terminal" if alias.startswith("terminal_") else "browser"
    assert resolve_shortcut(alias, focused_app) == resolve_shortcut(canonical, focused_app)


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
