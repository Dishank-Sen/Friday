"""Verify node: reconcile the last result with the screen and advance the loop.

This node is the single owner of the loop's progression fields: it advances
``step``, appends a decision+outcome record to ``history``, and tracks
``stuck_count`` (consecutive failed or screen-stalled steps). It never calls a
model and never interprets the free-text ``expected_result`` — that judgment
belongs to the next ``decide`` using the fresh screenshot. Everything here is
bookkeeping plus an injected screenshot diff and an optional read-only browser
probe.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from friday.harness.state import AgentState
from friday.harness.verify_diff import DiffResult, compare, step_outcome
from friday.harness.verify_settings import DiffSettings, VerifySettings

LOGGER = logging.getLogger(__name__)

ScreenshotLoader = Callable[[str], bytes]

# Input actions whose payload carries user-supplied text. Their carried values
# are never written into history, so typed text and clipboard contents cannot
# leak into a later prompt or log. Type actions are summarized by length.
_SENSITIVE_OPERATIONS: frozenset[str] = frozenset({"type", "key", "hold_key"})

# Outcome labels written into the history record.
_OUTCOMES = {"failed", "no_visible_change", "changed", "no_change_expected", "unknown"}

# Fixed hint text for a stalled step. Never includes page text, titles, URLs,
# or model text.
_HINT_NO_VISIBLE_CHANGE = (
    "Your last action had no visible effect on the screen. Try a different approach."
)
_HINT_STUCK = (
    "The last several actions did not change the screen. The run will stop if "
    "the screen does not change soon."
)


class BrowserProbe(Protocol):
    """A read-only probe of the active browser tab, or its absence."""

    def state(self) -> dict: ...
    def wait_ready(self, timeout_s: float) -> dict: ...


@dataclass(frozen=True, slots=True)
class VerifyDeps:
    """Injected dependencies for the verify node.

    ``load_screenshot`` reads a screenshot path into bytes (reusing decide's
    loader) and is used to detect unreadable/missing screenshots before the
    diff. ``probe`` is an optional read-only browser probe; when None (or
    failing) browser facts are simply absent. ``settings`` bounds the diff and
    the history.
    """

    load_screenshot: ScreenshotLoader
    settings: VerifySettings = field(default_factory=VerifySettings)
    probe: BrowserProbe | None = None


def verify(state: AgentState) -> dict:
    """Reconcile the last result; this wired pass-through stub performs no comparison."""
    LOGGER.info("harness verify stub ran")
    return {}


def make_verify(*, deps: VerifyDeps | None = None, stuck_limit: int | None = None) -> object:
    """Create a verify node that reconciles the last result and advances the loop.

    ``deps`` supplies the screenshot loader, settings, and optional probe.
    ``stuck_limit`` is a special-case override for the total number of
    consecutive failures that mark the run stuck (default from settings).

    Returns a partial state update writing ONLY ``step``, ``history``,
    ``stuck_count`` and ``hint``. It never writes status, final_report, prompt,
    pending_action, last_result, guard_verdict, or decision.
    """

    def run(state: AgentState) -> dict:
        LOGGER.info("harness verify ran")
        step = state.get("step", 0)
        decision = state.get("decision")
        pending = state.get("pending_action")
        last = state.get("last_result") or {}
        ok = bool(last.get("ok"))
        operation = _operation_name(last, pending)

        diff = _diff_for(state, diff_settings, loader)
        outcome = step_outcome(operation, ok, diff)

        entry = _history_record(
            decision=decision,
            pending=pending,
            operation=operation,
            ok=ok,
            outcome=outcome,
            last=last,
            diff=diff,
            settings=diff_settings,
            probe=probe,
        )

        history = list(state.get("history") or [])
        history = _bounded_history(history + [entry], diff_settings.max_history)

        update: dict = {"step": step + 1, "history": history}

        if outcome in {"failed", "no_visible_change"}:
            stuck = (state.get("stuck_count") or 0) + 1
            update["stuck_count"] = stuck
            if stuck >= stuck_limit_eff:
                update["hint"] = _HINT_STUCK
        elif outcome == "changed":
            update["stuck_count"] = 0

        if outcome == "no_visible_change" and not state.get("hint"):
            update["hint"] = _HINT_NO_VISIBLE_CHANGE

        return update

    diff_settings = deps.settings.diff if deps and deps.settings else DiffSettings()
    loader = deps.load_screenshot if deps else None
    probe = deps.probe if deps else None
    stuck_limit_eff = stuck_limit if stuck_limit is not None else (
        deps.settings.max_stuck if deps and deps.settings else 3
    )
    return run


def _operation_name(last: dict, pending: dict) -> str:
    """The canonical operation/action name of the executed step."""
    name = (
        last.get("operation")
        or (pending or {}).get("action")
        or (pending or {}).get("operation")
    )
    return str(name or "")


def _diff_for(state: AgentState, settings: DiffSettings, load: ScreenshotLoader | None):
    """Compute the screen diff, handling unusable screenshots as unreliable.

    ``load`` (injected, reusing decide's loader) is used to detect a missing or
    unreadable screenshot before the diff, so the node never lets a bad image
    raise out of verify.
    """
    prev = state.get("prev_screenshot_path")
    cur = state.get("screenshot_path")
    if not prev or not cur:
        return DiffResult(label="unreliable", changed_ratio=None)
    if load is not None:
        try:
            load(prev)
            load(cur)
        except (OSError, TypeError, ValueError):
            return DiffResult(label="unreliable", changed_ratio=None)
    return compare(prev, cur, settings)


def _history_record(
    *,
    decision: str | None,
    pending: dict,
    operation: str,
    ok: bool,
    outcome: str,
    last: dict,
    diff,
    settings: DiffSettings,
    probe: BrowserProbe | None,
) -> dict:
    """The bounded history record, matching the shape guard and facts read.

    Keeps ``decision``, ``action`` (the pending payload, sanitized) and
    ``outcome`` for the existing consumers, and adds step/operation/ok/error/
    expected_result/changed_ratio/browser facts.
    """
    record: dict = {
        "decision": decision,
        "outcome": outcome,
        "action": _sanitize_action(pending) if isinstance(pending, dict) else None,
    }
    if operation:
        record["operation"] = operation
    record["ok"] = bool(ok)
    if last.get("error") is not None:
        record["error"] = _bounded(last.get("error"), settings.max_action_summary)
    if diff is not None and diff.changed_ratio is not None and diff.changed_ratio != "":
        record["changed_ratio"] = round(float(diff.changed_ratio), 6)
    if isinstance(pending, dict) and pending.get("expected_result") is not None:
        record["expected_result"] = _bounded(
            pending.get("expected_result"), settings.max_action_summary
        )
    if probe is not None:
        facts = _browser_facts(probe)
        if facts:
            record["browser"] = facts
    return record


def _browser_facts(probe: BrowserProbe) -> dict | None:
    """A bounded, sanitized snapshot of the active browser tab, or None.

    Never returns page text, titles or URLs with query strings; only the
    bounded state fields a probe exposes. A failing probe yields None (no
    browser sub-record), never an exception.
    """
    try:
        state = probe.state()
    except Exception:
        return None
    if not isinstance(state, dict):
        return None
    return _sanitize_browser_state(state)


def _sanitize_action(pending: dict) -> dict:
    """Return the action without any sensitive carried value.

    For ``type``/``key``/``hold_key`` only the kind marker is kept, and a type
    action is summarized by its length, so the record carries the shape of what
    happened, never the text.
    """
    name = pending.get("action") or pending.get("operation")
    if name in _SENSITIVE_OPERATIONS:
        if isinstance(pending.get("text"), str):
            return {"action": name, "chars": len(pending.get("text", ""))}
        return {"action": name}
    return dict(pending)


def _bounded(value: object, limit: int) -> object:
    """Bound a value so the history record stays small."""
    if isinstance(value, str):
        return value if len(value) <= limit else value[:limit] + "…"
    if isinstance(value, dict):
        return {
            k: (v[:limit] + "…" if isinstance(v, str) and len(v) > limit else v)
            for k, v in value.items()
        }
    return value


def _sanitize_browser_state(state: dict) -> dict:
    """Strip query/fragment, and bound+sanitize untrusted browser text."""
    from urllib.parse import urlsplit

    out: dict = {}
    url = state.get("url")
    if isinstance(url, str) and url:
        try:
            parts = urlsplit(url)
            out["url"] = parts._replace(query="", fragment="").geturl()[ : 300]
        except ValueError:
            out["url"] = ""
    for key in ("title", "ready_state", "loading", "tab_count"):
        value = state.get(key)
        if isinstance(value, bool):
            out[key] = value
        elif isinstance(value, str):
            clean = "".join(ch for ch in value if ch.isalnum() or ch in " -_.:/#?&%+,")[:80]
            out[key] = clean if clean else ""
        elif value is None:
            out[key] = None
    return out


def _bounded_history(history: list, max_history: int) -> list:
    """Bound the total history length, summarizing oldest entries by dropping.

    Keeps the newest ``max_history`` entries; the existing readers already bound
    via facts, so dropping the oldest is consistent with how they consume it.
    """
    if len(history) <= max_history:
        return history
    return history[-max_history:]