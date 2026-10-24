"""Decide node stub."""

from __future__ import annotations

import logging

from friday.harness.state import AgentState

LOGGER = logging.getLogger(__name__)


def decide(state: AgentState) -> dict:
    """Build/call/parse the model, set decision/action, and own retries; this is a no-op."""
    LOGGER.info("harness decide stub ran")
    return {}
