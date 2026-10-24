from __future__ import annotations

from pathlib import Path

from friday.actions.focus import focused_app_for
from friday.desktop.observation import Observation, WindowInfo
from friday.harness.nodes.observe import make_observe
from friday.harness.state import initial_state
from friday.harness.trace import ObservationTraceWriter


class FakeClient:
    def __init__(self, responses: list[Observation | Exception]) -> None:
        self.responses = responses
        self.calls = 0

    def observation(self) -> Observation:
        response = self.responses[self.calls]
        self.calls += 1
        if isinstance(response, Exception):
            raise response
        return response


def _observation(windows: list[WindowInfo] | None = None) -> Observation:
    return Observation(
        screenshot_png=b"\x89PNG\r\n\x1a\n",
        screen_size=(1280, 720),
        windows=windows or [],
        active_window_id="0x00000001",
        active_window_class="Chromium",
        focused_app="browser",
    )


def test_observe_writes_only_observation_fields_and_safe_trace(tmp_path: Path) -> None:
    trace = ObservationTraceWriter(tmp_path)
    node = make_observe(FakeClient([_observation()]), trace, focused_app_for)

    update = node(initial_state("goal", 1))

    assert set(update) == {"screenshot_path", "screen_size", "windows", "focused_app"}
    assert update["screen_size"] == (1280, 720)
    assert Path(update["screenshot_path"]).read_bytes().startswith(b"\x89PNG")
    observation_json = (tmp_path / "observation.json").read_text(encoding="utf-8")
    assert "prompt" not in observation_json
    assert "screenshot_png" not in observation_json


def test_observe_retries_once_then_fails() -> None:
    client = FakeClient([RuntimeError("first"), RuntimeError("second")])
    node = make_observe(client, ObservationTraceWriter(Path("/tmp/unused")), focused_app_for)

    update = node(initial_state("goal", 1))

    assert client.calls == 2
    assert update == {"status": "failed", "final_report": "observation screenshot failed: second"}


def test_observe_keeps_nonfatal_empty_windows_from_client(tmp_path: Path) -> None:
    observation = _observation([])
    observation.focused_app = "other"
    node = make_observe(
        FakeClient([observation]), ObservationTraceWriter(tmp_path), focused_app_for
    )

    update = node(initial_state("goal", 1))

    assert update["windows"] == []
    assert update["screenshot_path"]
