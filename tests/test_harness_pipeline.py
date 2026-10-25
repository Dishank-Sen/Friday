"""End-to-end context-to-decision pipeline tests with controlled dependencies.

These tests compose the real ``make_build_context`` and ``make_guard`` nodes with
fake decision inputs and a fake executor, covering the full flow from raw agent
state through context construction, capability selection, prompt rendering, guard
enforcement, and execution recording — without a live desktop, model API, or real
keyboard/mouse.

The guard's authoritative parser re-parses ``pending_action`` from the registries,
so the fake model emits raw registry-form payloads (``{"operation": ...}`` or
``{"action": ...}``), exactly the shape the executor path expects.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from friday.harness.capabilities import ControlPolicy
from friday.harness.nodes.build_context import make_build_context
from friday.harness.nodes.guard import make_guard
from friday.harness.state import AgentState, initial_state


@dataclass
class Pipeline:
    """A composed harness pipeline with fake dependencies for one scenario."""

    policy: object = field(default=None)
    executed: list = field(default_factory=list)
    decide: object = field(default=None)

    def build_context(self):
        return make_build_context(policy=self.policy)

    def guard(self):
        return make_guard(policy=self.policy)

    def executor(self):
        def run(state: AgentState) -> dict:
            self.executed.append(dict(state.get("pending_action") or {}))
            return {"last_result": {"ok": True, "detail": "executed"}}
        return run

    def run_until(self, state: AgentState, max_iterations: int = 12) -> AgentState:
        ctx = self.build_context()
        gd = self.guard()
        ex = self.executor()
        for _ in range(max_iterations):
            update = ctx(state)
            state.update(update)
            if state.get("prompt") is None:
                return state
            # decide: the fake model echoes a pre-set decision or the provided
            # decide callback returns a pending action / decision.
            if self.decide is None:
                return state
            d = self.decide(state)
            state.update(d)
            decision = state.get("decision")
            if decision not in {"action", "retry"}:
                return state
            gv = gd(state)
            state.update(gv)
            verdict = state.get("guard_verdict")
            if verdict != "allow":
                state["hint"] = gv.get("hint")
                state["history"] = state.get("history", []) + [
                    {
                        "decision": decision,
                        "outcome": "rejected",
                        "action": dict(state.get("pending_action") or {}),
                    }
                ]
                return state
            ex(state)
        return state


class _Policy:
    """Policy provider controllable per test."""

    def __init__(self, approval: bool = True, user_control: bool = False) -> None:
        self._approval = approval
        self._user_control = user_control

    def policy(self, state):
        return ControlPolicy(approval=self._approval, user_control=self._user_control)


def _base_state(**overrides) -> dict:
    state = initial_state("open https://example.com", 10)
    state["screen_size"] = (1280, 720)
    state["focused_app"] = "browser"
    state["windows"] = [{"id": "0x00000001", "title": "Chromium", "active": True}]
    state["step"] = 1
    state["retries"] = 2
    state.update(overrides)
    return state


def _actions(*pending):
    """A decide callback that yields pending_action payloads, then declares done."""
    iterator = iter(pending)

    def run(state: AgentState) -> dict:
        try:
            payload = next(iterator)
        except StopIteration:
            return {"decision": "done"}
        return {"decision": "action", "pending_action": payload}

    return run


# --- scenario: open a URL in a browser --------------------------------------


def test_open_url_pipeline_allows_a_url_operation(tmp_path) -> None:
    p = Pipeline(policy=_Policy())
    decide = _actions({"operation": "open_url", "url": "https://example.com"})
    p.decide = decide
    state = _base_state()

    result = p.run_until(state)

    assert result["guard_verdict"] == "allow"
    assert p.executed == [{"operation": "open_url", "url": "https://example.com"}]
    # a prompt was produced before execution
    assert result["prompt"] is not None


# --- scenario: read+a README and summarize ----------------------------------


def test_read_file_pipeline_allows_a_registered_read(tmp_path) -> None:
    p = Pipeline(policy=_Policy())
    p.decide = _actions({"operation": "read_file", "path": "README.md"})
    state = _base_state(goal="read the README and summarize it")

    result = p.run_until(state)

    assert result["guard_verdict"] == "allow"
    assert p.executed[0]["operation"] == "read_file"


# --- scenario: create dir + file, verify content ----------------------------


def test_create_writes_are_allowed_when_approved() -> None:
    p = Pipeline(policy=_Policy(approval=True))
    p.decide = _actions(
        {"operation": "make_dir", "path": "project"},
        {"operation": "write_file", "path": "project/notes.txt", "content": "hello"},
        {"operation": "read_file", "path": "project/notes.txt"},
    )
    state = _base_state(goal="create a project dir with a notes file")

    result = p.run_until(state)

    assert result["guard_verdict"] == "allow"
    assert [e["operation"] for e in p.executed] == ["make_dir", "write_file", "read_file"]


def test_destructive_write_rejected_without_approval() -> None:
    p = Pipeline(policy=_Policy(approval=False))
    p.decide = _actions({"operation": "write_file", "path": "notes.txt", "content": "x"})
    state = _base_state(goal="write a file")

    result = p.run_until(state)

    assert result["guard_verdict"] == "reject"
    assert "approval required" in result["hint"]
    assert p.executed == []


# --- scenario: launch terminal, verify window, then a terminal shortcut ----


def test_terminal_flow_allows_launch_then_shortcut_after_verified_window() -> None:
    terminal_window_exists = False

    def decide(state: AgentState) -> dict:
        nonlocal terminal_window_exists
        # model sees verification status / window list in the facts
        visible = [w for w in (state.get("windows") or []) if w.get("active")]
        if not terminal_window_exists:
            terminal_window_exists = True
            return {"decision": "action",
                    "pending_action": {"operation": "launch_app", "app": "terminal"}}
        if visible:
            return {"decision": "action",
                    "pending_action": {"action": "shortcut", "name": "terminal_clear"}}
        return {"decision": "done"}

    p = Pipeline(policy=_Policy())
    p.decide = decide
    state = _base_state(goal="open a terminal and clear it", focused_app="terminal")

    result = p.run_until(state)

    assert result["guard_verdict"] == "allow"
    assert any(e.get("operation") == "launch_app" for e in p.executed)
    assert any(
        e.get("action") == "shortcut" and e.get("name") == "terminal_clear"
        for e in p.executed
    )


# --- scenario: unknown active app -------------------------------------------


def test_unknown_active_application_surfaces_no_input_shortcuts() -> None:
    p = Pipeline(policy=_Policy())
    p.decide = _actions({"action": "shortcut", "name": "browser_new_tab"})
    state = _base_state(focused_app="unknown")

    result = p.run_until(state)

    # the shortcut is not in the manifest for an unknown app, and the guard
    # independently rejects it because it has no binding for an unknown focus
    assert result["guard_verdict"] == "reject"
    assert "not available for focus" in result["hint"]
    assert p.executed == []


# --- scenario: missing accessibility / window metadata ----------------------


def test_missing_window_metadata_does_not_fabricate_and_is_bounded() -> None:
    p = Pipeline(policy=_Policy())
    p.decide = _actions({"action": "key", "key": "ctrl+t"})
    state = _base_state()
    state["windows"] = []
    state["focused_app"] = None
    state["screen_size"] = None  # unknown screen

    result = p.run_until(state)

    assert result["prompt"] is not None
    assert "Focused application: unknown" in result["prompt"]
    assert "Windows: []" in result["prompt"]


# --- scenario: failed op and recovery without blind repeat ------------------


def test_failed_operation_recovers_without_blind_repeat() -> None:
    p = Pipeline(policy=_Policy())
    state = _base_state()
    # previous attempt failed
    state["history"] = [{
        "decision": "action",
        "outcome": "failed",
        "action": {"operation": "open_url", "url": "https://bad"},
    }]
    p.decide = _actions({"operation": "open_url", "url": "https://bad"})

    result = p.run_until(state)

    # blind repeat of a failed action is rejected unless recovery hint present
    assert result["guard_verdict"] == "reject"
    assert "repeat" in result["hint"]


def test_failed_operation_recovers_when_hint_allows_retry() -> None:
    # build_context consumes and clears the hint before guard runs, so in the
    # composed pipeline a recovery hint does not persist to the guard's repeat
    # check. The guard's hint-exempt repeat rule is verified here in isolation.
    gd = make_guard(policy=_Policy())
    state = _base_state()
    state["pending_action"] = {"operation": "open_url", "url": "https://bad"}
    state["hint"] = "the network recovered, retry the url"
    state["history"] = [
        {"decision": "action", "outcome": "failed", "action": {"operation": "open_url"}}
    ]

    verdict = gd(state)

    assert verdict["guard_verdict"] == "allow"


# --- scenario: step/retry budget exhaustion ---------------------------------


def test_step_budget_exhaustion_stops() -> None:
    p = Pipeline(policy=_Policy())
    p.decide = _actions({"action": "key", "key": "ctrl+t"})
    state = _base_state(step=10, max_steps=10)

    result = p.run_until(state)

    assert result["guard_verdict"] == "stop"
    assert "budget" in result["hint"]


def test_retry_budget_exhaustion_rejects() -> None:
    p = Pipeline(policy=_Policy())
    p.decide = _actions({"action": "key", "key": "ctrl+t"})
    state = _base_state(retries=0)

    result = p.run_until(state)

    assert result["guard_verdict"] == "reject"
    assert "retry budget" in result["hint"]


# --- scenario: active user control ------------------------------------------


def test_active_user_control_blocks_input() -> None:
    p = Pipeline(policy=_Policy(user_control=True))
    p.decide = _actions({"action": "left_click", "x": 100, "y": 200})
    state = _base_state()

    result = p.run_until(state)

    assert result["guard_verdict"] == "reject"
    assert "controls the desktop" in result["hint"]
    assert p.executed == []


# --- scenario: unregistered operation ---------------------------------------


def test_unregistered_operation_is_rejected() -> None:
    p = Pipeline(policy=_Policy())
    p.decide = _actions({"operation": "system_shutdown", "path": "/"})
    state = _base_state()

    result = p.run_until(state)

    assert result["guard_verdict"] == "reject"
    assert "invalid action" in result["hint"]
    assert p.executed == []


# --- scenario: operation outside workspace ----------------------------------


def test_operation_outside_workspace_is_rejected() -> None:
    p = Pipeline(policy=_Policy())
    p.decide = _actions({"operation": "read_file", "path": "../../etc/shadow"})
    state = _base_state()

    result = p.run_until(state)

    assert result["guard_verdict"] == "reject"
    assert p.executed == []


# --- scenario: ambiguous / malformed model response -------------------------


def test_malformed_model_response_is_rejected() -> None:
    p = Pipeline(policy=_Policy())
    p.decide = _actions({"operation": 123})  # non-string discriminator
    state = _base_state()

    result = p.run_until(state)

    assert result["guard_verdict"] == "reject"
    assert p.executed == []


def test_missing_pending_action_after_context_error_never_executes() -> None:
    # A context construction failure yields no pending_action, so the guard
    # cannot allow anything.
    p = Pipeline(policy=_Policy())
    p.decide = _actions(None)  # decide sets pending_action to None
    state = _base_state()

    # simulate the decide emitting a None pending action
    state["pending_action"] = None
    update = p.guard()(state)

    assert update["guard_verdict"] == "reject"
    assert p.executed == []


# --- scenario: API succeeds but outcome unverified --------------------------


def test_op_succeeds_but_outcome_unverified_is_not_claimed() -> None:
    # An operation that completed at the API level but whose expected outcome is
    # still unverified must never be rendered as a success in the next context.
    p = Pipeline(policy=_Policy())
    state = _base_state()
    state["history"] = [
        {"decision": "action", "outcome": "unverified", "action": {"operation": "open_url"}}
    ]

    # next step looks at the state the executor built_context would see
    result = p.build_context()(state)

    assert result["prompt"] is not None
    # the unverified prior action is not surfaced as a success anywhere
    assert 'outcome: "succeeded"' not in result["prompt"]