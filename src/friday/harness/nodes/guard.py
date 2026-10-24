"""Guard node stub."""

from __future__ import annotations

import logging

from friday.harness.state import AgentState

LOGGER = logging.getLogger(__name__)


def guard(state: AgentState) -> dict:
    """Validate action/bounds/budgets/repeats/kill switch and set a verdict; no-op here."""
    LOGGER.info("harness guard stub ran")
    return {}
