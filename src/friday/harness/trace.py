"""Minimal safe trace writer for harness observations."""

from __future__ import annotations

import json
from pathlib import Path
from time import monotonic

from friday.desktop.observation import Observation


class ObservationTraceWriter:
    def __init__(self, trace_dir: Path) -> None:
        self._trace_dir = trace_dir

    def write(self, observation: Observation, error: str | None = None) -> str:
        """Write non-sensitive observation metadata and return the screenshot path."""
        self._trace_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = self._trace_dir / "screenshot.png"
        screenshot_path.write_bytes(observation.screenshot_png)
        payload = {
            "screenshot_path": str(screenshot_path),
            "screen_size": observation.screen_size,
            "windows": [window.model_dump() for window in observation.windows],
            "focused_app": observation.focused_app,
            "capture_error": error,
            "captured_at": monotonic(),
        }
        (self._trace_dir / "observation.json").write_text(json.dumps(payload), encoding="utf-8")
        return str(screenshot_path)
