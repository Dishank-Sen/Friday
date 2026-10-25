"""Server-side adapter exposing the read-only CDP browser probe to the API."""

from __future__ import annotations

import logging
from collections.abc import Callable

from friday.browser.cdp import CdpBrowserProbe
from friday.browser.models import BrowserState, ProbeStatus, WaitReady

LOGGER = logging.getLogger(__name__)

# A probe factory so tests can inject a fake; default builds a real CDP probe.
ProbeFactory = Callable[[], CdpBrowserProbe]


def default_probe_factory() -> CdpBrowserProbe:
    return CdpBrowserProbe()


class BrowserBackend:
    """Thin read-only facade over the debug browser probe.

    Every method fails safe: a missing/unreachable debug browser is reported as
    ``available=False`` (never an exception), on the assumption that a browser
    probe is a convenience — the harness runs fine without browser facts.
    """

    def __init__(self, factory: ProbeFactory = default_probe_factory) -> None:
        self._factory = factory

    def available(self) -> ProbeStatus:
        try:
            return ProbeStatus(available=self._factory().available())
        except Exception as error:
            LOGGER.info("browser probe available check failed: %s", error)
            return ProbeStatus(available=False)

    def state(self) -> BrowserState:
        try:
            return self._factory().state()
        except Exception as error:
            LOGGER.info("browser probe state failed: %s", error)
            return BrowserState()

    def wait_ready(self, timeout_s: float) -> WaitReady:
        try:
            return self._factory().wait_ready(timeout_s)
        except Exception as error:
            LOGGER.info("browser probe wait_ready failed: %s", error)
            return WaitReady(state="timeout", waited_ms=0)