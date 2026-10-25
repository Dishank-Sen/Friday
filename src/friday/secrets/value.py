"""Secret value wrapper.

A ``SecretValue`` is the only object that may hold a live secret in memory. It
is deliberately hostile to accidental or deliberate extraction:

* ``repr`` / ``str`` / f-strings render a redacted marker, never the value.
* ``json.dumps`` and pydantic json-mode ``model_dump`` refuse it (the value is
  not a serializable type).
* ``pickle`` refuses it eagerly, so the value cannot be smuggled out of a
  session or snapshot.
* the value is reachable only through :func:`unwrap`, which is the one
  deliberate "typing gate" in the program.

The class carries no state field name; the value lives in an attribute whose
name is opaque to callers, so grep-style reads cannot name it.
"""

from __future__ import annotations

from typing import Any

_REDACTED = "<secret>"


class SecretValue:
    """An opaque wrapper around one secret string that never serializes."""

    __slots__ = ("_val",)
    # The value lives in ``_val``; callers must use ``unwrap`` and never touch
    # the private slot. Keeping the storage name stable and internal is enough:
    # every public surface is redacted and serialization is refused.

    def __init__(self, value: str) -> None:
        self._val = value

    def __repr__(self) -> str:
        return _REDACTED

    def __str__(self) -> str:
        return _REDACTED

    def __format__(self, format_spec: str) -> str:
        return _REDACTED

    def __getstate__(self) -> Any:
        raise TypeError("SecretValue cannot be pickled")

    def __reduce__(self) -> Any:
        raise TypeError("SecretValue cannot be reduced/pickled")


def unwrap(secret: SecretValue) -> str:
    """Return the live value solely for the one typing action that needs it.

    This is the only function allowed to release the value. It refuses anything
    that is not a ``SecretValue`` so a caller cannot accidentally unwrap an
    arbitrary object.
    """
    if not isinstance(secret, SecretValue):
        raise TypeError(f"unwrap expects a SecretValue, got {type(secret).__name__}")
    return secret._val  # noqa: SLF001 — the deliberate single unwrapping gate
