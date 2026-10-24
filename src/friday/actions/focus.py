"""Class-name to focused-application mapping shared by host and server."""

from __future__ import annotations

FocusedApp = str

_EXACT = {
    "chromium": "browser",
    "xfce4-terminal": "terminal",
    "thunar-real": "file_manager",
    "org.xfce.mousepad": "text_editor",
}
_PREFIXES = (
    ("chromium", "browser"),
    ("xfce4-terminal", "terminal"),
    ("thunar", "file_manager"),
    ("org.xfce.mousepad", "text_editor"),
)


def focused_app_for(class_name: str | None) -> FocusedApp:
    """Return the known focused-app category for an X11 WM_CLASS value."""
    if not class_name:
        return "other"
    normalized = class_name.strip().lower()
    class_parts = [part.strip() for part in normalized.split("|") if part.strip()]
    dot_parts = [part for value in class_parts for part in value.split(".")]
    candidates = [normalized, *class_parts, *dot_parts]
    for part in candidates:
        if part in _EXACT:
            return _EXACT[part]
    for part in candidates:
        for prefix, focused_app in _PREFIXES:
            if part.startswith(prefix):
                return focused_app
    return "other"


IGNORED_WINDOW_CLASSES = frozenset({"xfce4-panel", "xfdesktop"})
