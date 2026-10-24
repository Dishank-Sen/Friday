"""Generate docs/operations.md from Friday's operation registry."""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path

from friday.operations.registry import INPUT_OPERATIONS, OPERATIONS

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "operations.md"
VERIFIED = """Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal."""


def render() -> str:
    lines = [
        "# Friday operations",
        "",
        "## Overview and conventions",
        "",
        "Coordinates are integer real-screen pixels. Operations use argv lists only; never shell strings. "
        "All server requests are Pydantic-validated before execution. URLs are limited to HTTP(S), "
        "window IDs use `^0x[0-9a-f]+$`, paths stay inside the configured workspace, and only Friday-started PIDs can be closed. "
        "Typed text, clipboard data, and file content must never be logged. Display work is serialized by one lock.",
        "",
        "## Summary",
        "",
        "| Operation | Category | Command |",
        "| --- | --- | --- |",
    ]
    for name, (category, argv, _) in INPUT_OPERATIONS.items():
        lines.append(f"| `{name}` | {category} | `{argv}` |")
    for definition in OPERATIONS.values():
        lines.append(f"| `{definition.name}` | {definition.category} | `{definition.argv}` |")
    for name, (category, argv, description) in INPUT_OPERATIONS.items():
        lines.extend(
            _section(
                name,
                category,
                description,
                argv,
                "existing action model",
                "unverified in this system-operations pass; existing executor behavior was not changed",
            )
        )
    for definition in OPERATIONS.values():
        fields = []
        for field_name, field in definition.model.model_fields.items():
            if field_name != "operation":
                fields.append(f"`{field_name}`: {field.annotation}")
        lines.extend(
            _section(
                definition.name,
                definition.category,
                definition.description,
                definition.argv,
                ", ".join(fields),
                VERIFIED,
            )
        )
    lines.extend(
        [
            "## Tools and packages",
            "",
            "The image installs `xdotool`, `scrot`, `wmctrl`, and `xclip`. Browser, terminal, file manager, and editor binaries are verified separately below.",
            "",
            "## Discrepancies",
            "",
            "`screen_size` is an authenticated API endpoint although the executor milestone described it as internal. `zoom` is host-only and therefore cannot be sent to `/operation` or `/action`.",
            "",
            "## Known issues",
            "",
            "`xdotool type` accepts non-ASCII input without returning an error in this image, but its rendered result was not machine-asserted. `set_clipboard` followed by `ctrl+v` is the recommended Unicode path because X11 clipboard content was read back exactly. `active_window` can fail when XFWM has no active client window.",
            "",
            "## Adding an operation",
            "",
            "Add one Pydantic model and `OperationDefinition` in `friday.operations.registry`, add argv and validation tests, run `python scripts/gen_operations_doc.py`, then commit the generated document.",
            "",
        ]
    )
    return "\n".join(lines)


def _section(
    name: str,
    category: str,
    description: str,
    argv: str,
    parameters: str,
    verification: str,
) -> list[str]:
    return [
        f"## `{name}`",
        "",
        f"- Category: {category}",
        f"- Description: {description}",
        f"- Parameters: {parameters or 'none'}",
        f"- Command: `{argv}`",
        "- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.",
        "- Timeout: 10 seconds unless the operation has an explicit timeout parameter.",
        "- Side effects/security: see registry validation; destructive actions are not undoable.",
        f"- Verification: {verification}",
        "",
    ]


if __name__ == "__main__":
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(render(), encoding="utf-8")
