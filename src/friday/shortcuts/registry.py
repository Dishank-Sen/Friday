"""The authoritative registry of named keyboard shortcuts."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import get_close_matches
from typing import Literal

from friday.actions.keys import normalize_key

Context = Literal["global", "text", "browser", "form", "window", "terminal", "file_manager"]
Status = Literal["verified", "unverified"]


@dataclass(frozen=True, slots=True)
class ShortcutDefinition:
    name: str
    keys: tuple[str, ...]
    context: Context
    description: str
    requires_focus: str
    expected_effect: str
    caveats: str
    risky: bool = False
    status: Status = "unverified"
    evidence: str = "Unverified pending container verification."


def _shortcut(
    name: str,
    keys: str | tuple[str, ...],
    context: Context,
    description: str,
    focus: str,
    effect: str,
    caveats: str = "",
    *,
    risky: bool = False,
) -> ShortcutDefinition:
    sequence = (keys,) if isinstance(keys, str) else keys
    return ShortcutDefinition(name, sequence, context, description, focus, effect, caveats, risky)


_ENTRIES = (
    _shortcut(
        "text_select_all", "ctrl+a", "text", "Select all text.", "any", "All text is selected."
    ),
    _shortcut(
        "text_copy",
        "ctrl+c",
        "text",
        "Copy selection.",
        "any",
        "Clipboard receives selection.",
        "Use terminal_copy in terminals.",
    ),
    _shortcut(
        "text_cut", "ctrl+x", "text", "Cut selection.", "any", "Selection is removed to clipboard."
    ),
    _shortcut(
        "text_paste", "ctrl+v", "text", "Paste clipboard.", "any", "Clipboard text is inserted."
    ),
    _shortcut("text_undo", "ctrl+z", "text", "Undo edit.", "any", "Most recent edit is reversed."),
    _shortcut(
        "text_redo",
        "ctrl+shift+z",
        "text",
        "Redo edit.",
        "any",
        "Undone edit is restored.",
        "Some apps use ctrl+y instead.",
    ),
    _shortcut("text_save", "ctrl+s", "text", "Save document.", "mousepad", "Document is saved."),
    _shortcut(
        "text_line_start",
        "Home",
        "text",
        "Move to line start.",
        "any",
        "Caret moves to line start.",
    ),
    _shortcut(
        "text_line_end", "End", "text", "Move to line end.", "any", "Caret moves to line end."
    ),
    _shortcut(
        "text_delete_word_back",
        "ctrl+BackSpace",
        "text",
        "Delete previous word.",
        "any",
        "Word before caret is removed.",
    ),
    _shortcut(
        "browser_focus_address_bar",
        "ctrl+l",
        "browser",
        "Focus address bar.",
        "chromium",
        "Address bar is focused.",
    ),
    _shortcut("browser_new_tab", "ctrl+t", "browser", "Open tab.", "chromium", "New tab appears."),
    _shortcut(
        "browser_close_tab", "ctrl+w", "browser", "Close tab.", "chromium", "Focused tab closes."
    ),
    _shortcut(
        "browser_next_tab", "ctrl+Tab", "browser", "Next tab.", "chromium", "Next tab is focused."
    ),
    _shortcut(
        "browser_prev_tab",
        "ctrl+shift+Tab",
        "browser",
        "Previous tab.",
        "chromium",
        "Previous tab is focused.",
    ),
    _shortcut(
        "browser_reload",
        "ctrl+r",
        "browser",
        "Reload page.",
        "chromium",
        "Focused tab reloads.",
        "F5 is also supported by Chromium.",
    ),
    _shortcut(
        "browser_back",
        "alt+Left",
        "browser",
        "Navigate back.",
        "chromium",
        "Previous history entry appears.",
    ),
    _shortcut(
        "browser_forward",
        "alt+Right",
        "browser",
        "Navigate forward.",
        "chromium",
        "Next history entry appears.",
    ),
    _shortcut(
        "browser_find", "ctrl+f", "browser", "Open find bar.", "chromium", "Find bar appears."
    ),
    _shortcut(
        "browser_zoom_in",
        "ctrl+plus",
        "browser",
        "Increase zoom.",
        "chromium",
        "Page zoom increases.",
    ),
    _shortcut(
        "browser_zoom_out",
        "ctrl+minus",
        "browser",
        "Decrease zoom.",
        "chromium",
        "Page zoom decreases.",
    ),
    _shortcut(
        "browser_zoom_reset",
        "ctrl+0",
        "browser",
        "Reset zoom.",
        "chromium",
        "Page zoom returns to 100%.",
    ),
    _shortcut(
        "browser_reopen_tab",
        "ctrl+shift+t",
        "browser",
        "Reopen closed tab.",
        "chromium",
        "Most recently closed tab reopens.",
    ),
    _shortcut("form_next_field", "Tab", "form", "Focus next field.", "any", "Focus advances."),
    _shortcut(
        "form_prev_field",
        "shift+Tab",
        "form",
        "Focus previous field.",
        "any",
        "Focus moves backward.",
    ),
    _shortcut(
        "form_submit",
        "Return",
        "form",
        "Submit focused form.",
        "any",
        "Form submits when supported.",
    ),
    _shortcut(
        "form_cancel",
        "Escape",
        "form",
        "Cancel focused UI.",
        "any",
        "Dialog or popup closes when supported.",
    ),
    _shortcut(
        "form_toggle",
        "space",
        "form",
        "Toggle focused control.",
        "any",
        "Checkbox or button toggles.",
    ),
    _shortcut(
        "form_option_up", "Up", "form", "Move option up.", "any", "Previous option is selected."
    ),
    _shortcut(
        "form_option_down", "Down", "form", "Move option down.", "any", "Next option is selected."
    ),
    _shortcut(
        "window_switch",
        "alt+Tab",
        "window",
        "Switch window.",
        "any",
        "Window switcher changes focus.",
    ),
    _shortcut(
        "window_close",
        "alt+F4",
        "window",
        "Close focused window.",
        "any",
        "Focused window closes.",
        risky=True,
    ),
    _shortcut(
        "window_maximize",
        "alt+F10",
        "window",
        "Toggle maximize.",
        "any",
        "Focused window maximizes or restores.",
    ),
    _shortcut(
        "window_minimize",
        "alt+F9",
        "window",
        "Minimize focused window.",
        "any",
        "Focused window minimizes.",
    ),
    _shortcut(
        "window_show_desktop",
        "ctrl+alt+d",
        "window",
        "Show desktop.",
        "any",
        "Windows hide to reveal desktop.",
    ),
    _shortcut(
        "terminal_interrupt",
        "ctrl+c",
        "terminal",
        "Interrupt foreground command.",
        "xfce4-terminal",
        "Foreground command receives SIGINT.",
        "Use text_copy in GUI text fields.",
        risky=True,
    ),
    _shortcut(
        "terminal_eof",
        "ctrl+d",
        "terminal",
        "Send EOF.",
        "xfce4-terminal",
        "Shell exits or input receives EOF.",
    ),
    _shortcut(
        "terminal_clear",
        "ctrl+l",
        "terminal",
        "Clear terminal.",
        "xfce4-terminal",
        "Terminal viewport clears.",
    ),
    _shortcut(
        "terminal_history_prev",
        "Up",
        "terminal",
        "Previous history entry.",
        "xfce4-terminal",
        "Previous command appears.",
    ),
    _shortcut(
        "terminal_copy",
        "ctrl+shift+c",
        "terminal",
        "Copy terminal selection.",
        "xfce4-terminal",
        "Clipboard receives selection.",
    ),
    _shortcut(
        "terminal_paste",
        "ctrl+shift+v",
        "terminal",
        "Paste into terminal.",
        "xfce4-terminal",
        "Clipboard text is pasted.",
    ),
    _shortcut(
        "file_rename",
        "F2",
        "file_manager",
        "Rename selected file.",
        "thunar",
        "Rename editor opens.",
    ),
    _shortcut(
        "file_new_folder",
        "ctrl+shift+n",
        "file_manager",
        "Create folder.",
        "thunar",
        "New-folder dialog opens.",
    ),
    _shortcut(
        "file_go_to_path",
        "ctrl+l",
        "file_manager",
        "Focus location entry.",
        "thunar",
        "Location entry is focused.",
    ),
    _shortcut(
        "file_delete_to_trash",
        "Delete",
        "file_manager",
        "Move selection to trash.",
        "thunar",
        "Selected files move to trash.",
        risky=True,
    ),
    _shortcut(
        "file_up",
        "alt+Up",
        "file_manager",
        "Open parent folder.",
        "thunar",
        "Parent directory appears.",
    ),
)

SHORTCUTS = {entry.name: entry for entry in _ENTRIES}


def resolve_shortcut(name: str) -> ShortcutDefinition:
    try:
        return SHORTCUTS[name]
    except KeyError as error:
        matches = get_close_matches(name, SHORTCUTS, n=3, cutoff=0.45)
        hint = f"; close matches: {', '.join(matches)}" if matches else ""
        raise ValueError(f"unknown shortcut: {name}{hint}") from error


def normalized_keys(shortcut: ShortcutDefinition) -> tuple[str, ...]:
    return tuple(normalize_key(key) for key in shortcut.keys)
