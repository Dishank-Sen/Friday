"""Named, focus-aware keyboard shortcuts."""

from .registry import SHORTCUTS, ShortcutDefinition, resolve_shortcut

__all__ = ["SHORTCUTS", "ShortcutDefinition", "resolve_shortcut"]
