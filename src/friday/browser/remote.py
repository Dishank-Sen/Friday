"""Host-side adapter exposing the container browser probe to the harness.

Implements the same read-only ``BrowserProbe`` shape the harness's ``verify``
node expects (``state() -> dict``, ``wait_ready(timeout_s) -> dict``) but talks
to the container's FastAPI endpoints through the desktop client rather than
holding a CDP connection. It is a thin, dependency-free mapping used only when
the focused app is a browser.
"""

from __future__ import annotations

import logging

from friday.desktop.client import DesktopClient
from friday.desktop.errors import DesktopError

LOGGER = logging.getLogger(__name__)


class RemoteBrowserProbe:
    """Read-only browser facts fetched from the container's probe endpoints."""

    def __init__(
        self,
        client: DesktopClient,
        *,
        available_timeout: float = 2.0,
    ) -> None:
        """Wrap a desktop client for browser probe requests.

        ``available_timeout`` bounds the availability check so a down debug
        browser does not stall the harness off our standard request timeout.
        """
        self._client = client
        self._available_timeout = available_timeout

    def available(self) -> bool:
        """Whether the container reports the debug browser reachable."""
        try:
            status = self._client.browser_status()
        except DesktopError as error:
            LOGGER.info("browser probe unavailable: %s", error)
            return False
        return status.available

    def state(self) -> dict:
        """:return: a sanitized snapshot of the active tab, or ``{}`` when down."""
        try:
            browser_state = self._client.browser_state()
        except DesktopError as error:
            LOGGER.info("browser probe state unavailable: %s", error)
            return {}
        return browser_state.model_dump()

    def wait_ready(self, timeout_s: float) -> dict:
        """:return: ``{"state": "ready"|"timeout", "waited_ms": int}``."""
        try:
            result = self._client.browser_wait_ready(timeout_s)
        except DesktopError as error:
            LOGGER.info("browser probe wait_ready unavailable: %s", error)
            return {"state": "timeout", "waited_ms": 0}
        return result.model_dump()