"""Guard node stub."""

from __future__ import annotations

import logging

from friday.harness.state import AgentState

LOGGER = logging.getLogger(__name__)


def guard(state: AgentState) -> dict:
    """Validate actions and budgets; this stub performs no validation or approval decision."""
    LOGGER.info("harness guard stub ran")
    return {}
