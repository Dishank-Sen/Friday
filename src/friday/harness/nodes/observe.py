"""Observe node stub."""

from __future__ import annotations

import logging

from friday.harness.state import AgentState

LOGGER = logging.getLogger(__name__)


def observe(state: AgentState) -> dict:
    """Capture first screenshot, screen size, and windows only; this stub writes no prompt."""
    LOGGER.info("harness observe stub ran")
    return {}
