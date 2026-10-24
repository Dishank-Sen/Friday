"""Decide node stub."""

from __future__ import annotations

import logging

from friday.harness.state import AgentState

LOGGER = logging.getLogger(__name__)


def decide(state: AgentState) -> dict:
    """Build and call the decision model; this stub performs no decision or retry handling."""
    LOGGER.info("harness decide stub ran")
    return {}
