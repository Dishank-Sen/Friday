"""Desktop client exceptions."""

from __future__ import annotations


class DesktopError(RuntimeError):
    """Base error returned by the desktop control client."""


class DesktopConnectionError(DesktopError):
    """The control server could not be reached."""


class DesktopTimeoutError(DesktopConnectionError):
    """The control server timed out responding to a request."""


class DesktopRequestError(DesktopError):
    """The control server rejected a request or command."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"desktop API returned {status_code}: {detail}")
