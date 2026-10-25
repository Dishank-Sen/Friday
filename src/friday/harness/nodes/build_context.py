"""Build-context node: prepares the next decision, never executes anything.

This node composes the independently tested components into a single decision
input. It collects and normalizes prompt facts, determines step policy, selects
capabilities, renders the model prompt, and returns only the fields the graph
needs. It never calls the LLM, runs operations/shortcuts/desktop actions, or
bypasses the guard.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Protocol

from friday.harness.capabilities import ControlPolicy, select_capabilities
from friday.harness.context import CapabilityManifest
from friday.harness.facts import FactLimits, NormalizedFacts, summarize_facts
from friday.harness.render import render_prompt
from friday.harness.state import AgentState

LOGGER = logging.getLogger(__name__)

Summarizer = Callable[[AgentState, ControlPolicy], NormalizedFacts]
Selector = Callable[[NormalizedFacts, ControlPolicy], CapabilityManifest]
Renderer = Callable[[NormalizedFacts, CapabilityManifest], str]


class PolicyProvider(Protocol):
    """Resolves the current approval / user-control status for one step."""

    def policy(self, state: AgentState) -> ControlPolicy: ...


def _default_policy(state: AgentState) -> ControlPolicy:
    """Conservative default policy: never assume approval.

    Approval and user-control status are *injected* dependencies (nothing in
    ``AgentState`` records them today), so the default does not assume approval
    and does not claim manual control. A caller-supplied ``PolicyProvider`` is
    what surfaces manual control; the guard remains the authority that
    independently blocks input regardless of this selection.
    """
    return ControlPolicy(approval=False, user_control=False)


def build_context(state: AgentState) -> dict:
    """Safe default with no dependencies; injected builders perform the real work."""
    LOGGER.info("harness build_context stub ran")
    return {}


def make_build_context(
    *,
    summarizer: Summarizer | None = None,
    selector: Selector | None = None,
    renderer: Renderer | None = None,
    policy: PolicyProvider | None = None,
    limits: FactLimits | None = None,
) -> Callable[[AgentState], dict]:
    """Create a build_context node with injectable dependencies.

    Each dependency defaults to the real component, so a caller may fake only
    what it wants to isolate. ``policy`` resolves the step's approval /
    user-control status; when omitted, ``_default_policy`` reads it from state.
    Limits are bound into the default summarizer (ignored when a custom
    summarizer is injected).

    Returns a partial state update: the rendered ``prompt`` and the consumed
    ``hint`` (build_context is the only writer of ``prompt`` and clears the hint
    it folds in). On dependency failure it returns an honest safe fallback
    (``prompt=None``) rather than fabricating context.
    """
    do_summarize = summarizer or _bind_summarize(limits)
    do_select = selector or _bind_select
    do_render = renderer or render_prompt
    resolve_policy = policy.policy if policy is not None else _default_policy

    def run(state: AgentState) -> dict:
        LOGGER.info("harness build_context ran")
        try:
            step_policy = resolve_policy(state)
            facts = do_summarize(state, step_policy)
            manifest = do_select(facts, step_policy)
            prompt = do_render(facts, manifest)
        except Exception:
            LOGGER.warning("harness build_context failed; safe fallback", exc_info=True)
            return {"prompt": None, "hint": None}
        return {"prompt": prompt, "hint": None}

    return run


def _bind_summarize(limits: FactLimits | None):
    """Bind default fact limits into ``summarize_facts`` for one node instance."""

    def summarize(state: AgentState, policy: ControlPolicy) -> NormalizedFacts:
        return summarize_facts(state, limits=limits, policy=policy)

    return summarize


def _bind_select(facts: NormalizedFacts, policy: ControlPolicy) -> CapabilityManifest:
    """Adapt ``select_capabilities``'s keyword-only signature to the node's shape."""
    return select_capabilities(facts=facts, policy=policy)