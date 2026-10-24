"""Observe node stub."""

from __future__ import annotations

import logging

from friday.harness.state import AgentState

LOGGER = logging.getLogger(__name__)


def observe(state: AgentState) -> dict:
    """Capture the first screenshot only; this stub performs no observation or file access."""
    LOGGER.info("harness observe stub ran")
    return {}
