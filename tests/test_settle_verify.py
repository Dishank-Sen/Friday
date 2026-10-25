"""Settle node: post-execution observation refresh."""

from __future__ import annotations

from friday.harness.nodes.settle import make_settle
from friday.harness.state import initial_state


class _Observation:
    def __init__(self) -> None:
        from friday.desktop.observation import WindowInfo

        self.screenshot_png = b"\x89PNG\r\n\x1a\n"
        self.screen_size = (1280, 720)
        self.windows = [WindowInfo(id="1", title="Chromium", class_name="Chromium", active=True)]
        self.active_window_class = "Chromium"
        self.focused_app = "browser"


class _Client:
    def __init__(self, observation=None) -> None:  # noqa: ANN001
        self._observation = observation or _Observation()
        self.calls = 0

    def observation(self):
        self.calls += 1
        return self._observation


class _FailingClient:
    def observation(self):
        raise RuntimeError("desktop unavailable")


class _Trace:
    def __init__(self) -> None:
        self.writes = 0

    def write(self, observation, error=None):  # noqa: ANN001
        self.writes += 1
        return f"/traces/screenshot-{self.writes}.png"


def _focus(table_class):  # noqa: ANN001, ANN202
    return "browser"


def _settle(client=None, trace=None, focus=None, probe=None):  # noqa: ANN001
    return make_settle(
        client or _Client(), trace or _Trace(), focus or _focus, probe=probe
    )


class _Probe:
    def __init__(self) -> None:
        self.calls = 0

    def wait_ready(self, timeout_s: float) -> dict:
        self.calls += 1
        return {"state": "ready", "waited_ms": int(timeout_s * 1000)}


class _FailingProbe:
    def wait_ready(self, timeout_s: float) -> dict:
        raise RuntimeError("probe down")


def _base(**overrides) -> dict:
    state = initial_state("open a web page", 10)
    state["step"] = 1
    state["retries"] = 2
    state["history"] = []
    state["screenshot_path"] = "/traces/screenshot-0.png"
    state["stuck_count"] = 0
    state.update(overrides)
    return state


# --- settle: post-execution refresh -----------------------------------------


def test_settle_rotates_prev_and_refreshes_capture_with_fresh_observation() -> None:
    client = _Client()
    trace = _Trace()
    node = _settle(client=client, trace=trace)
    state = _base(screenshot_path="/traces/previous.png")

    result = node(state)

    assert result["prev_screenshot_path"] == "/traces/previous.png"
    assert result["screenshot_path"].startswith("/traces/")
    assert client.calls == 1
    assert trace.writes == 1
    assert result["screen_size"] == (1280, 720)
    assert result["windows"] == [
        {"id": "1", "title": "Chromium", "class_name": "Chromium", "active": True}
    ]
    assert result["focused_app"] == "browser"


def test_settle_writes_only_its_contract_fields() -> None:
    result = _settle()(_base())

    assert set(result.keys()) == {
        "prev_screenshot_path",
        "screenshot_path",
        "screen_size",
        "windows",
        "focused_app",
    }


def test_settle_survives_observation_failure_without_losing_prior_path() -> None:
    node = _settle(client=_FailingClient())
    state = _base(screenshot_path="/traces/previous.png")

    result = node(state)

    # the prior capture is unchanged on failure; no fields are invented
    assert result.get("prev_screenshot_path") == "/traces/previous.png"
    assert "screenshot_path" not in result


# --- settle with the optional browser probe -----------------------------------


def test_settle_waits_for_page_when_focused_app_is_browser() -> None:
    probe = _Probe()
    client = _Client()
    node = _settle(client=client, trace=_Trace(), probe=probe)
    state = _base(screenshot_path="/traces/previous.png")
    state["focused_app"] = "browser"

    result = node(state)

    assert probe.calls == 1
    assert result["focused_app"] == "browser"


def test_settle_does_not_wait_when_focused_app_is_not_browser() -> None:
    probe = _Probe()
    node = _settle(client=_Client(), trace=_Trace(), probe=probe)
    state = _base(screenshot_path="/traces/previous.png")
    state["focused_app"] = "terminal"

    result = node(state)

    assert probe.calls == 0
    assert result["focused_app"] == "browser"  # focus_table returns the fresh class


def test_settle_does_not_wait_without_a_probe() -> None:
    node = _settle(client=_Client(), trace=_Trace(), probe=None)
    state = _base(screenshot_path="/traces/previous.png")
    state["focused_app"] = "browser"

    result = node(state)

    assert result["focused_app"] == "browser"


def test_settle_probe_failure_is_best_effort() -> None:
    node = _settle(client=_Client(), trace=_Trace(), probe=_FailingProbe())
    state = _base(screenshot_path="/traces/previous.png")
    state["focused_app"] = "browser"

    result = node(state)

    # a probe failure must not break settle's contract: capture still refreshes
    assert result["screenshot_path"].startswith("/traces/")
    assert result["focused_app"] == "browser"

