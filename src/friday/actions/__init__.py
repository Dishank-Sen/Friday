"""Shared desktop action models."""

from __future__ import annotations

from typing import Any

__all__ = ["Action", "ActionResult", "parse_action"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from .models import Action, ActionResult, parse_action

        return {"Action": Action, "ActionResult": ActionResult, "parse_action": parse_action}[name]
    raise AttributeError(name)
