"""Settle node stub."""

from __future__ import annotations

import logging

from friday.harness.state import AgentState

LOGGER = logging.getLogger(__name__)


def settle(state: AgentState) -> dict:
    """Capture stable image, rotate paths, refresh screen size/windows; this stub is a no-op."""
    LOGGER.info("harness settle stub ran")
    return {}
