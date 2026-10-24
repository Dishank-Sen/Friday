"""Settle node stub."""

from __future__ import annotations

import logging

from friday.harness.state import AgentState

LOGGER = logging.getLogger(__name__)


def settle(state: AgentState) -> dict:
    """Wait for screen stability and capture a screenshot; this stub performs neither."""
    LOGGER.info("harness settle stub ran")
    return {}
