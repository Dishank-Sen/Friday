"""Tests for the FastAPI browser probe endpoints."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from friday.browser.models import BrowserState, WaitReady
from server import app


class FakeBrowser:
    def __init__(self) -> None:
        self.state_value = BrowserState(url="https://x.example", tab_count=1)
        self.ready_value = WaitReady(state="ready", waited_ms=4)

    def state(self) -> BrowserState:
        return self.state_value

    def wait_ready(self, timeout_s: float) -> WaitReady:
        return self.ready_value

    def available(self):
        from friday.browser.models import ProbeStatus

        return ProbeStatus(available=True)


@pytest.fixture
def fake_browser(monkeypatch: pytest.MonkeyPatch) -> FakeBrowser:
    browser = FakeBrowser()
    monkeypatch.setattr(app, "_browser", lambda: browser)
    return browser


def test_browser_state_returns_state(fake_browser: FakeBrowser) -> None:
    result = app.browser_state()
    assert result.url == "https://x.example"
    assert result.tab_count == 1


def test_browser_wait_ready_valid_timeout(fake_browser: FakeBrowser) -> None:
    result = app.browser_wait_ready({"timeout_s": 5})
    assert result.state == "ready"
    assert result.waited_ms == 4


@pytest.mark.parametrize(
    "payload",
    [{"timeout_s": 0}, {"timeout_s": -1}, {"timeout_s": 31}, {"timeout_s": "x"}],
)
def test_browser_wait_ready_rejects_invalid_timeout(
    fake_browser: FakeBrowser, payload: dict
) -> None:
    with pytest.raises(HTTPException) as error:
        app.browser_wait_ready(payload)
    assert error.value.status_code == 422