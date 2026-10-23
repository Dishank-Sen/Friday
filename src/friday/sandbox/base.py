"""Backend-neutral sandbox interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Self


class Sandbox(ABC):
    @property
    @abstractmethod
    def api_url(self) -> str:
        """Base URL for the control API."""

    @property
    @abstractmethod
    def viewer_url(self) -> str:
        """URL for the desktop viewer."""

    @property
    @abstractmethod
    def token(self) -> str:
        """Bearer token for the control API."""

    @abstractmethod
    def start(self) -> None:
        """Start the sandbox and wait until it is usable."""

    @abstractmethod
    def stop(self) -> None:
        """Stop and clean up the sandbox."""

    @abstractmethod
    def wait_until_ready(self) -> None:
        """Wait until the control server passes its health check."""

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.stop()
