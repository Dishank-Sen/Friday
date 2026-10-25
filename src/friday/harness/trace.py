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
            "capture_error": error or observation.capture_error,
            "timings": {"captured_at": monotonic()},
        }
        (self._trace_dir / "observation.json").write_text(json.dumps(payload), encoding="utf-8")
        return str(screenshot_path)

    def write_image(self, step_index: int, name: str, png: bytes) -> str:
        """Save observation image bytes and return the path.

        ``name`` is collapsed to a plain basename and the step index is folded
        in, so hostile names cannot escape the trace folder. Returns the path in
        the same form as ``write`` returns the screenshot path.
        """
        self._trace_dir.mkdir(parents=True, exist_ok=True)
        safe = Path(name).name or "image"
        filename = f"{safe}-{step_index}.png"
        target = self._trace_dir / filename
        target.write_bytes(png)
        return str(target)
