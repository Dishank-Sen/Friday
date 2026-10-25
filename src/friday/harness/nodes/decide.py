"""Decide node: turn the rendered context into a model decision.

This node is the first real point where a model is invoked in the harness loop.
It reads the prompt that ``build_context`` rendered and the screenshot path that
``observe`` captured, calls an injected ``VisionLLM``, parses the response back
into the harness's existing ``Decision`` / ``pending_action`` shapes, and sets
them in state for the guard to enforce. It performs no execution itself.

The model call is the only I/O here. Everything else — reading state, parsing,
validating the response — is pure and deterministic, so the node stays easy to
test with a fake LLM.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path

from friday.harness.state import AgentState
from friday.llm.base import LLMResponse, VisionLLM

LOGGER = logging.getLogger(__name__)

_DECISIONS: frozenset[str] = frozenset({"action", "done", "retry", "fail"})


ScreenshotLoader = Callable[[str], bytes]


def _default_loader(path: str) -> bytes:
    return Path(path).read_bytes()


def decide(state: AgentState) -> dict:
    """Safe default with no dependencies; injected deciders perform the real work."""
    LOGGER.info("harness decide stub ran")
    return {}


def make_decide(
    *,
    llm: VisionLLM,
    load_screenshot: ScreenshotLoader | None = None,
) -> Callable[[AgentState], dict]:
    """Create a decide node that calls a model and parses its decision.

    ``llm`` is the injected model ("VisionLLM" contract: ``invoke(prompt,
    images)`` -> ``LLMResponse``). ``load_screenshot`` turns the state's
    ``screenshot_path`` into image bytes; it defaults to reading the file from
    disk.

    Returns a partial state update for the guard: ``decision`` (one of the
    ``Decision`` literals), the parsed ``pending_action`` (set only when the
    decision is ``action`` and the model supplied one), and ``retries`` bumped
    once when the decision is ``retry``. On any failure to obtain or
    parse a model decision the node reports an honest ``fail`` rather than
    fabricating an action the model never proposed.
    """
    loader = load_screenshot or _default_loader

    def run(state: AgentState) -> dict:
        LOGGER.info("harness decide ran")
        prompt = state.get("prompt")
        if not prompt:
            return _fail_by_default("no prompt to decide on")
        screenshot_path = state.get("screenshot_path")
        try:
            images = [loader(screenshot_path)] if screenshot_path else []
            response = llm.invoke(prompt, images)
        except (OSError, TypeError, ValueError, RuntimeError) as error:
            LOGGER.warning("harness decide model call failed: %s", error)
            return _fail_by_default("model call failed")
        parsed = _parse_response(response)
        if parsed is None:
            LOGGER.warning("harness decide could not parse a valid decision response")
            return _fail_by_default("model returned an unparsable decision")

        decision = parsed["decision"]
        update: dict = {"decision": decision}
        if decision == "action":
            pending = parsed.get("pending_action")
            update["pending_action"] = pending if isinstance(pending, dict) else {}
        if decision == "retry":
            update["retries"] = state.get("retries", 0) + 1
        return update

    return run


def _parse_response(response: LLMResponse) -> dict | None:
    """Parse the model text into a minimal validated decision payload."""
    try:
        data = json.loads(response.text)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    decision = data.get("decision")
    if decision not in _DECISIONS:
        return None
    return {
        "decision": decision,
        "pending_action": data.get("pending_action"),
        "retried": data.get("retried"),
    }


def _fail_by_default(reason: str) -> dict:
    LOGGER.info("harness decide no usable decision: %s", reason)
    return {"decision": "fail", "hint": reason}