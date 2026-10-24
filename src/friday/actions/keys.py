from __future__ import annotations

import re

_ALIASES = {
    "cmd": "super",
    "control": "ctrl",
    "del": "Delete",
    "down": "Down",
    "end": "End",
    "enter": "Return",
    "esc": "Escape",
    "home": "Home",
    "left": "Left",
    "meta": "super",
    "minus": "minus",
    "pgdn": "Page_Down",
    "pgup": "Page_Up",
    "right": "Right",
    "plus": "plus",
    "space": "space",
    "tab": "Tab",
    "up": "Up",
    "win": "super",
}
_MODIFIERS = {"alt", "ctrl", "shift", "super"}
_NAMED_KEYS = {
    "BackSpace",
    "Delete",
    "Down",
    "End",
    "Escape",
    "Home",
    "Insert",
    "Left",
    "Page_Down",
    "Page_Up",
    "Return",
    "Right",
    "Tab",
    "Up",
    "space",
}
_FUNCTION_KEY = re.compile(r"f(?:[1-9]|1[0-2])$", re.IGNORECASE)
_LETTER_OR_DIGIT = re.compile(r"^[a-z0-9]$", re.IGNORECASE)


def normalize_key(key: str) -> str:
    if not key.strip():
        raise ValueError("key cannot be empty")
    normalized: list[str] = []
    for token in key.split("+"):
        normalized.append(_normalize_token(token))
    return "+".join(normalized)


def _normalize_token(token: str) -> str:
    candidate = token.strip()
    if not candidate:
        raise ValueError("key contains an empty token")
    lowered = candidate.lower()
    alias = _ALIASES.get(lowered)
    if alias is not None:
        return alias
    if lowered in _MODIFIERS:
        return lowered
    if _LETTER_OR_DIGIT.fullmatch(candidate):
        return lowered
    if _FUNCTION_KEY.fullmatch(candidate):
        return candidate.upper()
    if candidate in _NAMED_KEYS:
        return candidate
    raise ValueError(f"invalid key token: {candidate}")
