"""Finish node stub."""

from __future__ import annotations

import logging

from friday.harness.state import AgentState

LOGGER = logging.getLogger(__name__)


def finish(state: AgentState) -> dict:
    """Set terminal status and write the final report; this stub performs neither."""
    LOGGER.info("harness finish stub ran")
    return {}
