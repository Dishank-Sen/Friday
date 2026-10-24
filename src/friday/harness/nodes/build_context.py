"""Build-context node stub."""

from __future__ import annotations

import logging

from friday.harness.state import AgentState

LOGGER = logging.getLogger(__name__)


def build_context(state: AgentState) -> dict:
    """Assemble deterministic next-prompt inputs; this stub assembles no context."""
    LOGGER.info("harness build_context stub ran")
    return {}
