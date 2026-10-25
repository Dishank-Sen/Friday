"""Read-only browser probe for the harness.

Package ``__init__`` imports only the dependency-free probe pieces (the CDP
probe and the shared models). ``RemoteBrowserProbe`` deliberately lives in
``friday.browser.remote`` and is imported from there, because it depends on
``DesktopClient``; importing it here would create an import cycle when
``friday.desktop.client`` imports ``friday.browser.models``.
"""

from friday.browser.cdp import CDP_ENDPOINT, BrowserProbeError, CdpBrowserProbe
from friday.browser.models import (
    BrowserState,
    ProbeStatus,
    WaitReady,
    clean_title,
    strip_url,
)

__all__ = [
    "BrowserProbeError",
    "BrowserState",
    "CdpBrowserProbe",
    "CDP_ENDPOINT",
    "ProbeStatus",
    "WaitReady",
    "clean_title",
    "strip_url",
]