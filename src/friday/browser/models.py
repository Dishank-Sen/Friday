"""Shared models for the read-only browser probe.

The probe reports a bounded, sanitized snapshot of the active browser tab so the
harness's ``verify`` node can record objective browser facts. The models are
deliberately read-only: a probe never clicks, types, navigates, reads page
content, the DOM, cookies or storage. Only ``BrowserState`` and ``WaitReady``
cross the server/client boundary.

``BrowserState`` only ever carries the four fields the harness observes: the
page ``url``, ``title``, document ``ready_state`` and whether the tab is still
``loading``, plus the number of open ``tab_count``. Untrusted text (URL and
title) is sanitized and bounded by the server before it is returned, and again
by ``verify`` when it records the facts.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

MAX_URL_LENGTH = 300
MAX_TITLE_LENGTH = 80
_KEPT_URL_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
                           "0123456789 -_.:/#?&%+@")
_KEPT_TITLE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
                              "0123456789 -_.:/#?&%+,")


def _clean(value: str | None, kept: frozenset[str], limit: int) -> str | None:
    if value is None:
        return None
    cleaned = "".join(ch for ch in value if ch in kept)
    return cleaned if len(cleaned) <= limit else cleaned[:limit]


def clean_title(value: str | None) -> str | None:
    """Sanitize and bound a page title so it never carries control chars or grows unbounded."""
    return _clean(value, _KEPT_TITLE_CHARS, MAX_TITLE_LENGTH)


def strip_url(value: str) -> str | None:
    """Return the URL with query string and fragment removed and bounded.

    Keeps scheme, host and path (plus a possible trailing slash), truncated to
    ``MAX_URL_LENGTH``. A value that is not a plausible URL yields ``None``.
    """
    from urllib.parse import urlsplit

    if not value:
        return None
    try:
        parts = urlsplit(value)
    except ValueError:
        return None
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return None
    stripped = parts._replace(query="", fragment="").geturl()
    return stripped if len(stripped) <= MAX_URL_LENGTH else stripped[:MAX_URL_LENGTH]


class BrowserState(BaseModel):
    """A read-only snapshot of the active browser tab."""

    model_config = ConfigDict(extra="forbid")

    url: str | None = Field(default=None, max_length=MAX_URL_LENGTH)
    title: str | None = Field(default=None, max_length=MAX_TITLE_LENGTH)
    ready_state: str | None = Field(default=None, max_length=32)
    loading: bool = False
    tab_count: int = Field(default=0, ge=0)


class WaitReady(BaseModel):
    """Result of waiting for the active tab to become ready."""

    model_config = ConfigDict(extra="forbid")

    state: str  # "ready" or "timeout"
    waited_ms: int = Field(default=0, ge=0)


class ProbeStatus(BaseModel):
    """Whether the debug browser is reachable; used as a circuit-breaker signal."""

    model_config = ConfigDict(extra="forbid")

    available: bool