"""Tests for the server-side browser backend (read-only probe facade)."""

from __future__ import annotations

from friday.browser.models import BrowserState, WaitReady
from server.backend.browser import BrowserBackend


class FakeProbe:
    def __init__(self, *, state=None, ready=None, available=True, raise_on="") -> None:
        self._state = state or BrowserState(url="https://x.example", title="GitHub")
        self._ready = ready or WaitReady(state="ready", waited_ms=3)
        self._available = available
        self._raise_on = raise_on

    def available(self) -> bool:
        if "available" in self._raise_on:
            raise RuntimeError("down")
        return self._available

    def state(self) -> BrowserState:
        if "state" in self._raise_on:
            raise RuntimeError("down")
        return self._state

    def wait_ready(self, timeout_s: float) -> WaitReady:
        if "wait_ready" in self._raise_on:
            raise RuntimeError("down")
        return self._ready


def test_available_reflects_probe() -> None:
    backend = BrowserBackend(lambda: FakeProbe(available=True))
    assert backend.available().available is True


def test_available_false_when_probe_down() -> None:
    backend = BrowserBackend(lambda: FakeProbe(available=True, raise_on="available"))
    assert backend.available().available is False


def test_state_returns_sanitized_browser_state() -> None:
    backend = BrowserBackend(lambda: FakeProbe())
    state = backend.state()
    assert state.url == "https://x.example"
    assert state.title == "GitHub"


def test_state_empty_when_probe_raises() -> None:
    backend = BrowserBackend(lambda: FakeProbe(raise_on="state"))
    assert backend.state() == BrowserState()


def test_wait_ready_delegates() -> None:
    backend = BrowserBackend(lambda: FakeProbe())
    result = backend.wait_ready(5.0)
    assert result.state == "ready"
    assert result.waited_ms == 3


def test_wait_ready_timeout_when_probe_raises() -> None:
    backend = BrowserBackend(lambda: FakeProbe(raise_on="wait_ready"))
    result = backend.wait_ready(5.0)
    assert result.state == "timeout"
    assert result.waited_ms == 0