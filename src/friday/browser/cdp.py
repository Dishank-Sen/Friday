"""Read-only browser probe over Chrome DevTools Protocol.

This module runs inside the container, next to the desktop ``chromium``. It
connects to the debug browser over CDP against the loopback-only address
``http://127.0.0.1:<port>`` and reads a bounded snapshot of the active tab. It
is strictly read-only: it never clicks, types, navigates, evaluates arbitrary
scripts, reads page content/the DOM, cookies or storage, and it never calls
``close()`` on a page or browser context — on shutdown it only disconnects.

``playwright`` is imported lazily so host-side code and tests never need it
installed; the module fails cleanly (a probe reports ``available=False``) when
Playwright or the debug browser is absent. The server instantiates one
``CdpBrowserProbe`` per request and guarantees a single tab (Chromium launched
with ``--remote-debugging-port`` and a separate ``--user-data-dir``).
"""

from __future__ import annotations

import logging
import time
from typing import Any

from friday.browser.models import BrowserState, WaitReady, strip_url

LOGGER = logging.getLogger(__name__)

CDP_ENDPOINT = "http://127.0.0.1:9222"


class BrowserProbeError(RuntimeError):
    """The debug browser is not reachable over CDP."""


class CdpBrowserProbe:
    """Connect to the debug Chromium over CDP and read active-tab facts."""

    def __init__(self, endpoint: str = CDP_ENDPOINT) -> None:
        self._endpoint = endpoint
        self._playwright = None

    def _pw(self) -> Any:
        if self._playwright is None:
            try:
                import playwright.sync_api  # noqa: PLC0415
            except ImportError as error:  # pragma: no cover - import guard
                raise BrowserProbeError(
                    "playwright is not installed in the server environment"
                ) from error
            self._playwright = playwright.sync_api
        return self._playwright

    def available(self) -> bool:
        """Whether Playwright and a CDP endpoint appear reachable.

        Fails safe: returns False on any import, connection or protocol error
        so a missing browser never raises out of the server.
        """
        try:
            pw = self._pw()
            with pw.sync_playwright() as p:
                p.chromium.connect_over_cdp(self._endpoint)
        except Exception as error:
            LOGGER.info("browser probe unavailable: %s", error)
            return False
        return True

    def state(self) -> BrowserState:
        """Read the active tab's url, title, ready state and tab count."""
        pw = self._pw()
        with pw.sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(self._endpoint)
            try:
                context = browser.contexts[0] if browser.contexts else None
                pages = list(context.pages) if context else []
                page = next((page for page in pages if page is not None), None)
                tab_count = len(pages)
                if page is None:
                    return BrowserState(tab_count=tab_count, loading=False)
                return BrowserState(
                    url=strip_url(page.url) if page.url else None,
                    title=page.title() if page.title else None,
                    ready_state=_ready_state(page),
                    loading=bool(getattr(page, "is_loading", lambda: False)()),
                    tab_count=tab_count,
                )
            finally:
                browser.close()  # closes the connection, never the browser

    def wait_ready(self, timeout_s: float) -> WaitReady:
        """Wait for the active tab to reach ``complete``/load, then read state.

        Returns ``state="ready"`` if the page reported a complete document
        within the timeout, else ``"timeout"``. The read is still bounded so an
        error path returns a ``timeout`` result rather than raising.
        """
        pw = self._pw()
        started = time.monotonic()
        with pw.sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(self._endpoint)
            try:
                context = browser.contexts[0] if browser.contexts else None
                page = next((pg for pg in (context.pages if context else [])), None)
                if page is None:
                    return WaitReady(state="timeout", waited_ms=_elapsed_ms(started))
                try:
                    page.wait_for_load_state("load", timeout=timeout_s * 1000)
                except Exception:
                    return WaitReady(state="timeout", waited_ms=_elapsed_ms(started))
                return WaitReady(state="ready", waited_ms=_elapsed_ms(started))
            finally:
                browser.close()

    def close(self) -> None:
        """Nothing to release; the browser is only disconnected, never closed."""
        return None


def _ready_state(page: Any) -> str | None:
    try:
        state = page.evaluate("document.readyState")
    except Exception:
        return None
    return str(state) if isinstance(state, str) and state in {
        "loading", "interactive", "complete",
    } else None


def _elapsed_ms(started: float) -> int:
    return int(round((time.monotonic() - started) * 1000))