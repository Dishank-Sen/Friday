"""Injected observation node implementation."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Protocol

from friday.desktop.observation import Observation
from friday.harness.state import AgentState

LOGGER = logging.getLogger(__name__)


class ObservationClient(Protocol):
    def observation(self) -> Observation: ...


class TraceWriter(Protocol):
    def write(self, observation: Observation, error: str | None = None) -> str: ...


def observe(state: AgentState) -> dict:
    """Safe default with no dependencies; injected observers perform the real capture."""
    LOGGER.info("harness observe stub ran")
    return {}


def make_observe(
    client: ObservationClient,
    trace_writer: TraceWriter,
    focus_table: Callable[[str | None], str],
) -> Callable[[AgentState], dict]:
    """Create an observation node with explicit desktop and trace dependencies."""

    def run(state: AgentState) -> dict:
        LOGGER.info("harness observe ran")
        try:
            observation = client.observation()
        except Exception:
            LOGGER.warning("harness observation failed; retrying", exc_info=True)
            try:
                observation = client.observation()
            except Exception as error:
                message = f"observation screenshot failed: {error}"
                LOGGER.error(message)
                return {"status": "failed", "final_report": message}
        screenshot_path = trace_writer.write(observation)
        return {
            "screenshot_path": screenshot_path,
            "screen_size": observation.screen_size,
            "windows": [window.model_dump() for window in observation.windows],
            "focused_app": focus_table(observation.active_window_class),
        }

    return run
