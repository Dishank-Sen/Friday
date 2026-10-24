"""Executor node stub."""

from __future__ import annotations

import logging

from friday.harness.state import AgentState

LOGGER = logging.getLogger(__name__)


def executor(state: AgentState) -> dict:
    """Run the pending action and record its result; this stub performs no execution."""
    LOGGER.info("harness executor stub ran")
    return {}
