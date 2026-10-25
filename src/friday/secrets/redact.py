"""Redaction: scrub secret values from text and from logging output."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable

from friday.secrets.value import SecretValue, unwrap

_MARKER = "<secret>"


def redact(text: str, *secrets: SecretValue) -> str:
    """Replace every occurrence of any secret value with a fixed marker.

    This is used at trust boundaries (trace writes, log emission, http error
    bodies) to ensure a value that leaked into a message on its way out is
    stripped before it is persisted or surfaced. The marker is constant, so no
    amount of surrounding value also appearing is a leak.
    """
    out = text
    for secret in secrets:
        out = out.replace(unwrap(secret), _MARKER)
    return out


class LoggingFilter(logging.Filter):
    """A logging filter that redacts every active secret from each record.

    ``provider`` is a zero-arg callable returning the current ``SecretValue``
    set (for example a closure over a vault), so the filter always sees the
    live secrets and never caches a stale value.
    """

    def __init__(
        self,
        provider: Callable[[], Iterable[SecretValue]],
        name: str = "",
    ) -> None:
        super().__init__(name=name)
        self._provider = provider

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        if isinstance(record.msg, str):
            record.msg = redact(record.msg, *self._provider())
        if record.args:
            redacted_args: tuple[object, ...] = tuple(
                (redact(str(arg), *self._provider()) if isinstance(arg, str) else arg)
                for arg in record.args
            )
            record.args = redacted_args
        return True
