"""Live secret storage.

The vault holds secrets by name only and returns opaque :class:`SecretValue`
handles. Nothing here logs, records, or inspects values; the runner stores a
secret once and the rest of the program works exclusively through
``SecretValue`` / :func:`~friday.secrets.unwrap`.
"""

from __future__ import annotations

from typing import Protocol

from friday.secrets.value import SecretValue


class SecretVault(Protocol):
    """Dependency the runner stores secrets into and nodes read names from."""

    def names(self) -> frozenset[str]: ...
    def contains(self, name: str) -> bool: ...
    def get(self, name: str) -> SecretValue | None: ...
    def store(self, name: str, secret: SecretValue) -> None: ...
    def drop(self, name: str) -> None: ...


class MemorySecretVault:
    """In-process vault backed by a plain dict. For CLI/terminal secrets."""

    def __init__(self) -> None:
        self._entries: dict[str, SecretValue] = {}

    def names(self) -> frozenset[str]:
        return frozenset(self._entries)

    def contains(self, name: str) -> bool:
        return name in self._entries

    def get(self, name: str) -> SecretValue | None:
        return self._entries.get(name)

    def store(self, name: str, secret: SecretValue) -> None:
        self._entries[name] = secret

    def drop(self, name: str) -> None:
        self._entries.pop(name, None)
