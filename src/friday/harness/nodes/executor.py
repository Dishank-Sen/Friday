"""Executor node stub."""

from __future__ import annotations

import logging

from friday.harness.state import AgentState

LOGGER = logging.getLogger(__name__)


def executor(state: AgentState) -> dict:
    """Run pending action and record expected failures in last_result; this stub is a no-op."""
    LOGGER.info("harness executor stub ran")
    return {}
