"""Tests for the host-side RemoteBrowserProbe adapter."""

from __future__ import annotations

from friday.browser.models import BrowserState, ProbeStatus, WaitReady
from friday.browser.remote import RemoteBrowserProbe
from friday.desktop.errors import DesktopRequestError


class FakeClient:
    def __init__(self) -> None:
        self.status: ProbeStatus | None = None
        self.state: BrowserState | None = None
        self.ready: WaitReady | None = None
        self.fail: type[Exception] | None = None

    def browser_status(self) -> ProbeStatus:
        if self.fail:
            raise self.fail
        assert self.status is not None
        return self.status

    def browser_state(self) -> BrowserState:
        if self.fail:
            raise self.fail
        assert self.state is not None
        return self.state

    def browser_wait_ready(self, timeout_s: float) -> WaitReady:
        if self.fail:
            raise self.fail
        assert self.ready is not None
        return self.ready


def test_available_true_when_container_reports_reachable() -> None:
    client = FakeClient()
    client.status = ProbeStatus(available=True)
    probe = RemoteBrowserProbe(client)
    assert probe.available() is True


def test_available_false_when_container_reports_down() -> None:
    client = FakeClient()
    client.status = ProbeStatus(available=False)
    probe = RemoteBrowserProbe(client)
    assert probe.available() is False


def test_available_false_on_request_error() -> None:
    client = FakeClient()
    client.fail = DesktopRequestError(502, "down")
    probe = RemoteBrowserProbe(client)
    assert probe.available() is False


def test_state_returns_sanitized_snapshot() -> None:
    client = FakeClient()
    client.state = BrowserState(url="https://x.example", title="GitHub", tab_count=2)
    probe = RemoteBrowserProbe(client)
    assert probe.state() == {
        "url": "https://x.example",
        "title": "GitHub",
        "ready_state": None,
        "loading": False,
        "tab_count": 2,
    }


def test_state_empty_when_probe_down() -> None:
    client = FakeClient()
    client.fail = DesktopRequestError(502, "down")
    probe = RemoteBrowserProbe(client)
    assert probe.state() == {}


def test_wait_ready_maps_success() -> None:
    client = FakeClient()
    client.ready = WaitReady(state="ready", waited_ms=120)
    probe = RemoteBrowserProbe(client)
    assert probe.wait_ready(5.0) == {"state": "ready", "waited_ms": 120}


def test_wait_ready_timeout_on_error() -> None:
    client = FakeClient()
    client.fail = DesktopRequestError(502, "down")
    probe = RemoteBrowserProbe(client)
    assert probe.wait_ready(5.0) == {"state": "timeout", "waited_ms": 0}