"""Verify node stub."""

from __future__ import annotations

import logging

from friday.harness.state import AgentState

LOGGER = logging.getLogger(__name__)


def verify(state: AgentState) -> dict:
    """Compare pre/post screenshots; this wired pass-through stub performs no comparison."""
    LOGGER.info("harness verify stub ran")
    return {}
