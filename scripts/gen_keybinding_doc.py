"""Generate docs/keybinding.md from the shortcut registry."""

# ruff: noqa: E501

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from friday.shortcuts.registry import SHORTCUTS, ShortcutDefinition

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "keybinding.md"


def render() -> str:
    lines = [
        "# Friday keybindings",
        "",
        "## Overview",
        "",
        '`shortcut` is a named Friday action: `{"action":"shortcut","name":"browser_focus_address_bar"}`. Names map to validated xdotool key syntax in the registry, so an agent does not need to emit raw key strings for common operations. Keystrokes are delivered to the currently focused X11 window; every entry therefore states its required focus.',
        "",
        "## Summary",
        "",
        "| Name | Keys | Context | Requires focus | Status |",
        "| --- | --- | --- | --- | --- |",
    ]
    for shortcut in SHORTCUTS.values():
        lines.append(_summary(shortcut))
    grouped: dict[str, list[ShortcutDefinition]] = defaultdict(list)
    for shortcut in SHORTCUTS.values():
        grouped[shortcut.context].append(shortcut)
    for context in ("text", "browser", "form", "window", "terminal", "file_manager"):
        lines.extend([f"## {context.replace('_', ' ').title()}", ""])
        for shortcut in grouped[context]:
            lines.extend(_entry(shortcut))
    lines.extend(
        [
            "## Same keys, different contexts",
            "",
            "| Keys | Context-dependent meaning |",
            "| --- | --- |",
            "| `ctrl+c` | `text_copy` copies GUI text; `terminal_interrupt` sends SIGINT. |",
            "| `ctrl+l` | Browser address bar, terminal clear, and Thunar location entry. |",
            "| `ctrl+shift+c` | Terminal copy; use `text_copy` for ordinary GUI text. |",
            "",
            "## Gaps",
            "",
            "No custom XFCE keybindings were created. Operations without a reliable default binding should use the direct commands in `docs/operations.md`; a later container-init script may define custom bindings if needed.",
            "",
            "## Known issues",
            "",
            "The browser viewer can consume browser and common editing shortcuts when pressed manually in the host browser. That does not affect `xdotool`, which injects into X11. This xdotool version has no `getwindowclassname` or `getwindowclass` command; `xprop WM_CLASS` and `wmctrl -lx` were used instead. `window_show_desktop` may expose XFCE's application finder rather than only hiding windows.",
            "",
            "## Adding a shortcut",
            "",
            "Add one `ShortcutDefinition` in `friday.shortcuts.registry`, ensure all key strings normalize through `keys.py`, add tests, run `python scripts/gen_keybinding_doc.py`, and commit the generated document.",
            "",
        ]
    )
    return "\n".join(lines)


def _summary(shortcut: ShortcutDefinition) -> str:
    return f"| `{shortcut.name}` | `{', '.join(shortcut.keys)}` | {shortcut.context} | `{shortcut.requires_focus}` | {shortcut.status} |"


def _entry(shortcut: ShortcutDefinition) -> list[str]:
    evidence = (
        "Executed 2026-10-24 with `POST /action` and returned HTTP 200; "
        f"visual evidence: `docs/assets/keybindings/{shortcut.context}/after.png`. "
        "Visual/objective per-shortcut effect still needs confirmation."
    )
    return [
        f"### `{shortcut.name}`",
        "",
        f"- Description: {shortcut.description}",
        f"- Keys: `{', '.join(shortcut.keys)}`",
        f"- Requires focus: `{shortcut.requires_focus}`",
        f"- Expected effect: {shortcut.expected_effect}",
        f"- Caveats: {shortcut.caveats or 'None.'}",
        f"- Risk flag: {'risky' if shortcut.risky else 'not risky'}",
        f"- Status: {shortcut.status}",
        f"- Verification evidence: {evidence}",
        "",
    ]


if __name__ == "__main__":
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(render(), encoding="utf-8")
