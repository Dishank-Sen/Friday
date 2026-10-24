"""The authoritative registry of logical, focus-aware keyboard shortcuts."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import get_close_matches
from typing import Literal

from friday.actions.keys import normalize_key

Context = Literal["global", "text", "browser", "form", "window", "terminal", "file_manager"]
FocusedApp = Literal["browser", "terminal", "file_manager", "text_editor", "other"]
Status = Literal["verified", "unverified"]
Binding = tuple[str, ...] | None


class ShortcutNotAvailable(ValueError):
    """A known shortcut has no binding for the focused application."""

    def __init__(self, name: str, focused_app: str, available_contexts: list[str]) -> None:
        self.name = name
        self.focused_app = focused_app
        self.available_contexts = available_contexts
        available = ", ".join(available_contexts) or "none"
        super().__init__(f"{name} is available in: {available}; the focused app is {focused_app}")


@dataclass(frozen=True, slots=True)
class ShortcutDefinition:
    name: str
    bindings: dict[str, Binding]
    context: Context
    description: str
    expected_effect: str
    caveats: str
    risky: bool = False
    status: Status = "unverified"
    evidence: str = "Unverified pending container verification."


def _shortcut(
    name: str,
    bindings: dict[str, str | tuple[str, ...] | None],
    context: Context,
    description: str,
    effect: str,
    caveats: str = "",
    *,
    risky: bool = False,
) -> ShortcutDefinition:
    normalized = {
        focused_app: None if keys is None else ((keys,) if isinstance(keys, str) else keys)
        for focused_app, keys in bindings.items()
    }
    return ShortcutDefinition(name, normalized, context, description, effect, caveats, risky)


_ENTRIES = (
    _shortcut(
        "copy",
        {"default": "ctrl+c", "terminal": "ctrl+shift+c"},
        "text",
        "Copy selection.",
        "Clipboard receives selection.",
        "ctrl+c interrupts a terminal program.",
    ),
    _shortcut(
        "cut",
        {"default": "ctrl+x", "terminal": None},
        "text",
        "Cut selection.",
        "Selection is removed to clipboard.",
    ),
    _shortcut(
        "paste",
        {"default": "ctrl+v", "terminal": "ctrl+shift+v"},
        "text",
        "Paste clipboard.",
        "Clipboard text is inserted.",
    ),
    _shortcut(
        "select_all",
        {"default": "ctrl+a", "terminal": "ctrl+shift+a"},
        "text",
        "Select all.",
        "All selectable content is selected.",
    ),
    _shortcut(
        "undo",
        {"default": "ctrl+z", "terminal": None},
        "text",
        "Undo edit.",
        "Most recent edit is reversed.",
    ),
    _shortcut(
        "redo",
        {"default": "ctrl+shift+z", "terminal": None},
        "text",
        "Redo edit.",
        "Undone edit is restored.",
        "Some apps use ctrl+y.",
    ),
    _shortcut(
        "save",
        {"default": "ctrl+s", "terminal": None},
        "text",
        "Save document.",
        "Document is saved.",
    ),
    _shortcut(
        "find",
        {"default": "ctrl+f", "terminal": "ctrl+shift+f"},
        "text",
        "Open find UI.",
        "Find UI appears.",
    ),
    _shortcut(
        "text_line_start",
        {"default": "Home"},
        "text",
        "Move to line start.",
        "Caret moves to line start.",
    ),
    _shortcut(
        "text_line_end", {"default": "End"}, "text", "Move to line end.", "Caret moves to line end."
    ),
    _shortcut(
        "text_delete_word_back",
        {"default": "ctrl+BackSpace"},
        "text",
        "Delete previous word.",
        "Word before caret is removed.",
    ),
    _shortcut(
        "browser_focus_address_bar",
        {"browser": "ctrl+l"},
        "browser",
        "Focus address bar.",
        "Address bar is focused.",
    ),
    _shortcut("browser_new_tab", {"browser": "ctrl+t"}, "browser", "Open tab.", "New tab appears."),
    _shortcut(
        "browser_close_tab", {"browser": "ctrl+w"}, "browser", "Close tab.", "Focused tab closes."
    ),
    _shortcut(
        "browser_next_tab",
        {"browser": "ctrl+Tab"},
        "browser",
        "Focus next tab.",
        "Next tab is focused.",
    ),
    _shortcut(
        "browser_prev_tab",
        {"browser": "ctrl+shift+Tab"},
        "browser",
        "Focus previous tab.",
        "Previous tab is focused.",
    ),
    _shortcut(
        "browser_reload",
        {"browser": "ctrl+r"},
        "browser",
        "Reload page.",
        "Focused tab reloads.",
        "F5 also reloads Chromium.",
    ),
    _shortcut(
        "browser_back",
        {"browser": "alt+Left"},
        "browser",
        "Navigate back.",
        "Previous history entry appears.",
    ),
    _shortcut(
        "browser_forward",
        {"browser": "alt+Right"},
        "browser",
        "Navigate forward.",
        "Next history entry appears.",
    ),
    _shortcut(
        "browser_zoom_in",
        {"browser": "ctrl+plus"},
        "browser",
        "Increase zoom.",
        "Page zoom increases.",
    ),
    _shortcut(
        "browser_zoom_out",
        {"browser": "ctrl+minus"},
        "browser",
        "Decrease zoom.",
        "Page zoom decreases.",
    ),
    _shortcut(
        "browser_zoom_reset",
        {"browser": "ctrl+0"},
        "browser",
        "Reset zoom.",
        "Page zoom returns to 100%.",
    ),
    _shortcut(
        "browser_reopen_tab",
        {"browser": "ctrl+shift+t"},
        "browser",
        "Reopen closed tab.",
        "Last closed tab reopens.",
    ),
    _shortcut(
        "form_next_field", {"default": "Tab"}, "form", "Focus next field.", "Focus advances."
    ),
    _shortcut(
        "form_prev_field",
        {"default": "shift+Tab"},
        "form",
        "Focus previous field.",
        "Focus moves backward.",
    ),
    _shortcut(
        "form_submit", {"default": "Return"}, "form", "Submit form.", "Form submits when supported."
    ),
    _shortcut(
        "form_cancel",
        {"default": "Escape"},
        "form",
        "Cancel focused UI.",
        "Dialog or popup closes when supported.",
    ),
    _shortcut(
        "form_toggle", {"default": "space"}, "form", "Toggle control.", "Focused control toggles."
    ),
    _shortcut(
        "form_option_up",
        {"default": "Up"},
        "form",
        "Move option up.",
        "Previous option is selected.",
    ),
    _shortcut(
        "form_option_down",
        {"default": "Down"},
        "form",
        "Move option down.",
        "Next option is selected.",
    ),
    _shortcut(
        "window_switch",
        {"default": "alt+Tab"},
        "window",
        "Switch window.",
        "Window switcher changes focus.",
    ),
    _shortcut(
        "window_close",
        {"default": "alt+F4"},
        "window",
        "Close window.",
        "Focused window closes.",
        risky=True,
    ),
    _shortcut(
        "window_maximize",
        {"default": "alt+F10"},
        "window",
        "Toggle maximize.",
        "Focused window maximizes or restores.",
    ),
    _shortcut(
        "window_minimize",
        {"default": "alt+F9"},
        "window",
        "Minimize window.",
        "Focused window minimizes.",
    ),
    _shortcut(
        "window_show_desktop",
        {"default": "ctrl+alt+d"},
        "window",
        "Show desktop.",
        "Windows hide to reveal desktop.",
    ),
    _shortcut(
        "terminal_interrupt",
        {"terminal": "ctrl+c"},
        "terminal",
        "Interrupt foreground command.",
        "Foreground command receives SIGINT.",
        risky=True,
    ),
    _shortcut(
        "terminal_eof",
        {"terminal": "ctrl+d"},
        "terminal",
        "Send EOF.",
        "Shell exits or input receives EOF.",
    ),
    _shortcut(
        "terminal_clear",
        {"terminal": "ctrl+l"},
        "terminal",
        "Clear terminal.",
        "Terminal viewport clears.",
    ),
    _shortcut(
        "terminal_history_prev",
        {"terminal": "Up"},
        "terminal",
        "Previous history entry.",
        "Previous command appears.",
    ),
    _shortcut(
        "file_rename",
        {"file_manager": "F2"},
        "file_manager",
        "Rename selected file.",
        "Rename editor opens.",
    ),
    _shortcut(
        "file_new_folder",
        {"file_manager": "ctrl+shift+n"},
        "file_manager",
        "Create folder.",
        "New-folder dialog opens.",
    ),
    _shortcut(
        "file_go_to_path",
        {"file_manager": "ctrl+l"},
        "file_manager",
        "Focus location entry.",
        "Location entry is focused.",
    ),
    _shortcut(
        "file_delete_to_trash",
        {"file_manager": "Delete"},
        "file_manager",
        "Move selection to trash.",
        "Selection moves to trash.",
        risky=True,
    ),
    _shortcut(
        "file_up",
        {"file_manager": "alt+Up"},
        "file_manager",
        "Open parent folder.",
        "Parent directory appears.",
    ),
)

SHORTCUTS = {entry.name: entry for entry in _ENTRIES}
ALIASES = {
    "text_copy": "copy",
    "terminal_copy": "copy",
    "text_cut": "cut",
    "text_paste": "paste",
    "terminal_paste": "paste",
    "text_select_all": "select_all",
    "text_undo": "undo",
    "text_redo": "redo",
    "text_save": "save",
    "browser_find": "find",
}


def shortcut_definition(name: str) -> ShortcutDefinition:
    """Look up a logical name or a deprecated alias without resolving focus."""
    canonical = ALIASES.get(name, name)
    try:
        return SHORTCUTS[canonical]
    except KeyError as error:
        matches = get_close_matches(name, [*SHORTCUTS, *ALIASES], n=3, cutoff=0.45)
        hint = f"; close matches: {', '.join(matches)}" if matches else ""
        raise ValueError(f"unknown shortcut: {name}{hint}") from error


def resolve_shortcut(name: str, focused_app: str) -> list[str]:
    """Resolve a logical shortcut against fresh focused-app information."""
    definition = shortcut_definition(name)
    if focused_app in definition.bindings:
        keys = definition.bindings[focused_app]
    else:
        keys = definition.bindings.get("default")
    if keys is None:
        available = sorted(key for key, value in definition.bindings.items() if value is not None)
        raise ShortcutNotAvailable(name, focused_app, available)
    return [normalize_key(key) for key in keys]
