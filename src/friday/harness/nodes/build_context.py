"""Build-context node stub."""

from __future__ import annotations

import logging

from friday.harness.state import AgentState

LOGGER = logging.getLogger(__name__)


def build_context(state: AgentState) -> dict:
    """Only writer of deterministic prompt; consumes hint and clears it; this stub is a no-op."""
    LOGGER.info("harness build_context stub ran")
    return {}
