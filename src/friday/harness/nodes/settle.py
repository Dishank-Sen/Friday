"""Settle node: capture a stable post-execution image and refresh screen context."""

from __future__ import annotations

import logging
from collections.abc import Callable

from friday.harness.state import AgentState

LOGGER = logging.getLogger(__name__)


def settle(state: AgentState) -> dict:
    """Capture stable image, rotate paths, refresh screen size/windows; this stub is a no-op."""
    LOGGER.info("harness settle stub ran")
    return {}


def make_settle(
    client: object,
    trace_writer: object,
    focus_table: Callable[[str | None], str],
    probe: object | None = None,
    wait_timeout_s: float = 5.0,
) -> Callable[[AgentState], dict]:
    """Create a settle node that refreshes the observation after an action.

    After the executor runs an action, the screen has changed. This node takes a
    fresh observation, rotates ``screenshot_path`` into ``prev_screenshot_path``,
    and rewrites ``screenshot_path`` / ``screen_size`` / ``windows`` /
    ``focused_app`` so ``verify`` and the next ``build_context`` see current
    state. On a capture failure it leaves the prior capture in place and returns
    no path field (fail-closed on the refresh), rather than claiming a new state
    it did not observe.

    When an optional read-only ``probe`` is supplied and the focused app is a
    browser, it first calls ``probe.wait_ready(wait_timeout_s)`` so the fresh
    capture is of a page that has finished loading. The wait is best-effort: a
    probe failure, absence or timeout never breaks settle's contract — the
    capture and refresh proceed as usual.
    """

    def run(state: AgentState) -> dict:
        LOGGER.info("harness settle ran")
        update: dict = {}
        previous = state.get("screenshot_path")
        if previous:
            update["prev_screenshot_path"] = previous
        if probe is not None and state.get("focused_app") == "browser":
            _wait_for_page(probe, wait_timeout_s)
        try:
            observation = client.observation()
        except Exception as error:
            LOGGER.warning("harness settle observation refresh failed: %s", error)
            return update
        path = trace_writer.write(observation)
        update["screenshot_path"] = path
        update["screen_size"] = observation.screen_size
        update["windows"] = [window.model_dump() for window in observation.windows]
        update["focused_app"] = focus_table(observation.active_window_class)
        return update

    return run


def _wait_for_page(probe: object, timeout_s: float) -> None:
    """Best-effort wait for the active browser tab to finish loading."""
    if not hasattr(probe, "wait_ready"):
        return
    try:
        probe.wait_ready(timeout_s)
    except Exception as error:
        LOGGER.info("harness settle browser wait_ready failed: %s", error)