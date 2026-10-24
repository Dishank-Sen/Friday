"""Generate docs/keybinding.md from the focus-aware shortcut registry."""

# ruff: noqa: E501

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "keybinding.md"
_APPS = ("browser", "terminal", "file_manager", "text_editor", "other")

if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from friday.shortcuts.registry import ALIASES, SHORTCUTS, ShortcutDefinition  # noqa: E402


def render() -> str:
    lines = [
        "# Friday keybindings",
        "",
        "## Overview",
        "",
        '`shortcut` is a named action: `{"action":"shortcut","name":"copy"}`. Logical names resolve against a fresh active-window lookup immediately before key injection, so the agent does not need to emit raw keys. `default` bindings apply to any focused app without an explicit binding; an explicit `n/a` does not fall back. Deprecated aliases remain accepted for compatibility.',
        "",
        "## Binding matrix",
        "",
        "| Name | Browser | Terminal | File manager | Text editor | Other | Status |",
        "| --- | --- | --- | --- | --- | --- | --- |",
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
            "## Deprecated aliases",
            "",
            "| Alias | Logical name |",
            "| --- | --- |",
            *[f"| `{alias}` | `{name}` |" for alias, name in ALIASES.items()],
            "",
            "## Same keys, different contexts",
            "",
            "| Keys | Meaning |",
            "| --- | --- |",
            "| `ctrl+c` | `copy` normally copies; `terminal_interrupt` sends SIGINT. |",
            "| `ctrl+l` | Browser address bar, terminal clear, and file-manager location entry. |",
            "| `ctrl+shift+c` | `copy` in a terminal. |",
            "",
            "## Gaps",
            "",
            "No custom XFCE keybindings are created. Unavailable shortcuts return a helpful failure; use direct operations from `docs/operations.md` until a later container-init task adds a custom binding.",
            "",
            "## Known issues",
            "",
            "The browser viewer can swallow shortcuts pressed manually in the host browser; xdotool injection into X11 is unaffected. Entries marked unverified need an objective or visual check in the current image.",
            "",
            "## Adding a shortcut",
            "",
            "Add one logical registry entry with bindings, test all focused-app resolutions, run `python scripts/gen_keybinding_doc.py`, and commit this generated document.",
            "",
        ]
    )
    return "\n".join(lines)


def _binding(shortcut: ShortcutDefinition, focused_app: str) -> str:
    if focused_app in shortcut.bindings:
        keys = shortcut.bindings[focused_app]
    else:
        keys = shortcut.bindings.get("default")
    return "n/a" if keys is None else ", ".join(keys)


def _summary(shortcut: ShortcutDefinition) -> str:
    values = " | ".join(f"`{_binding(shortcut, app)}`" for app in _APPS)
    return f"| `{shortcut.name}` | {values} | {shortcut.status} |"


def _entry(shortcut: ShortcutDefinition) -> list[str]:
    bindings = ", ".join(f"{app}: {_binding(shortcut, app)}" for app in _APPS)
    return [
        f"### `{shortcut.name}`",
        "",
        f"- Description: {shortcut.description}",
        f"- Bindings: {bindings}",
        f"- Expected effect: {shortcut.expected_effect}",
        f"- Caveats: {shortcut.caveats or 'None.'}",
        f"- Risk flag: {'risky' if shortcut.risky else 'not risky'}",
        f"- Status: {shortcut.status}",
        f"- Verification evidence: {shortcut.evidence}",
        "",
    ]


if __name__ == "__main__":
    OUTPUT.write_text(render(), encoding="utf-8")
