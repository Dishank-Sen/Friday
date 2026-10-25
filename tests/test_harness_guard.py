from __future__ import annotations

from friday.harness.capabilities import ControlPolicy
from friday.harness.nodes.guard import make_guard
from friday.harness.state import initial_state


def _state(**overrides) -> dict:
    state = initial_state("open a web page", 10)
    state["focused_app"] = "browser"
    state["screen_size"] = (1280, 720)
    state["step"] = 1
    state["retries"] = 2
    state["history"] = []
    state.update(overrides)
    return state


class _Policy:
    def __init__(self, approval: bool = True, user_control: bool = False) -> None:
        self._policy = ControlPolicy(approval=approval, user_control=user_control)

    def policy(self, state):
        return self._policy


def _guard(**kwargs):
    kwargs.setdefault("policy", _Policy())
    return make_guard(**kwargs)


def _reject(hint: str) -> dict:
    return {"guard_verdict": "reject", "hint": hint}


# --- no proposal can never authorize -----------------------------------------


def test_no_pending_action_cannot_authorize() -> None:
    node = _guard()
    assert node(_state(pending_action=None)) == _reject("no pending action to validate")


def test_non_dict_pending_action_is_rejected() -> None:
    node = _guard()
    assert node(_state(pending_action="open_url")) == _reject("no pending action to validate")


def test_context_construction_error_cannot_lead_to_execution() -> None:
    # If build_context failed, pending_action is absent; the guard must reject.
    node = _guard()
    assert node(_state(pending_action=None))["guard_verdict"] == "reject"


# --- independent of capability manifest --------------------------------------


def test_invented_operation_name_is_rejected_despite_manifest() -> None:
    node = _guard()
    pending = {"operation": "delete_everything", "path": "/home/user"}

    result = node(_state(pending_action=pending))

    assert result["guard_verdict"] == "reject"
    assert "invalid action" in result["hint"]


def test_invented_action_type_is_rejected() -> None:
    node = _guard()
    pending = {"action": "sudo_rm_rf", "target": "/"}

    result = node(_state(pending_action=pending))

    assert result["guard_verdict"] == "reject"
    assert "invalid action" in result["hint"]


def test_omitted_capability_in_manifest_still_enforced_by_registry() -> None:
    # A valid, registered operation that the manifest did not list is still
    # gated by the registry + approval checks, independently of the manifest.
    pending = {"operation": "close_window", "window_id": "0x00000001"}

    denied = _guard(policy=_Policy(approval=False))(_state(pending_action=pending))
    assert denied["guard_verdict"] == "reject"

    allowed = _guard(policy=_Policy(approval=True))(_state(pending_action=pending))
    assert allowed["guard_verdict"] == "allow"


# --- schema / parameter validation -------------------------------------------


def test_malformed_operation_parameters_are_rejected() -> None:
    node = _guard()
    # open_url requires http(s) scheme; a raw `file:` URI is invalid and rejected
    pending = {"operation": "open_url", "url": "file:///etc/passwd"}

    result = node(_state(pending_action=pending))

    assert result["guard_verdict"] == "reject"


def test_workspace_path_escape_is_rejected() -> None:
    node = _guard()
    pending = {"operation": "read_file", "path": "../etc/shadow"}

    result = node(_state(pending_action=pending))

    assert result["guard_verdict"] == "reject"


def test_bad_window_id_is_rejected() -> None:
    node = _guard()
    pending = {"operation": "focus_window", "window_id": "not-a-hex-id"}

    result = node(_state(pending_action=pending))

    assert result["guard_verdict"] == "reject"


# --- coordinate bounds -------------------------------------------------------


def test_coordinate_outside_screen_bounds_is_rejected() -> None:
    node = _guard()
    pending = {"action": "left_click", "x": 5000, "y": 9999}

    result = node(_state(pending_action=pending))

    assert result["guard_verdict"] == "reject"
    assert "out of bounds" in result["hint"]


def test_negative_coordinate_is_rejected() -> None:
    node = _guard()
    pending = {"action": "mouse_move", "x": -5, "y": 100}

    result = node(_state(pending_action=pending))

    assert result["guard_verdict"] == "reject"


def test_in_bounds_coordinate_is_allowed() -> None:
    node = _guard()
    pending = {"action": "left_click", "x": 100, "y": 200}

    result = node(_state(pending_action=pending))

    assert result["guard_verdict"] == "allow"


# --- budgets -----------------------------------------------------------------


def test_step_budget_exhaustion_stops() -> None:
    node = _guard()
    pending = {"action": "left_click", "x": 100, "y": 200}

    result = node(_state(pending_action=pending, step=10, max_steps=10))

    assert result["guard_verdict"] == "stop"
    assert "budget" in result["hint"]


def test_retry_budget_exhaustion_rejects() -> None:
    node = _guard()
    pending = {"action": "left_click", "x": 100, "y": 200}

    result = node(_state(pending_action=pending, retries=0))

    assert result["guard_verdict"] == "reject"
    assert "retry budget" in result["hint"]


def _clock_at(value: float):
    def clock() -> float:
        return value

    return clock


class _BudgetConfig:
    workspace_root = "/config/friday-workspace"
    approval_required_categories = frozenset({"files", "processes", "windows"})
    max_seconds = 10.0


def test_time_budget_exhaustion_stops() -> None:
    node = _guard(config=_BudgetConfig(), clock=_clock_at(100.0))
    pending = {"action": "left_click", "x": 100, "y": 200}

    result = node(_state(pending_action=pending, started_at=10.0))

    assert result["guard_verdict"] == "stop"
    assert "time budget" in result["hint"]


def test_within_time_budget_allows() -> None:
    node = _guard(config=_BudgetConfig(), clock=_clock_at(15.0))
    pending = {"action": "left_click", "x": 100, "y": 200}

    result = node(_state(pending_action=pending, started_at=10.0))

    assert result["guard_verdict"] == "allow"


def test_unset_started_at_skips_time_budget() -> None:
    node = _guard(config=_BudgetConfig(), clock=_clock_at(100.0))
    pending = {"action": "left_click", "x": 100, "y": 200}
    # started_at stays 0.0 (initial_state default): the time check is skipped
    result = node(_state(pending_action=pending, started_at=0.0))

    assert result["guard_verdict"] == "allow"


# --- approval ----------------------------------------------------------------


def test_destructive_operation_requires_approval() -> None:
    pending = {"operation": "delete_file", "path": "notes.txt"}

    allowed = _guard(policy=_Policy(approval=True))(_state(pending_action=pending))
    denied = _guard(policy=_Policy(approval=False))(_state(pending_action=pending))

    assert allowed["guard_verdict"] == "allow"
    assert denied["guard_verdict"] == "reject"
    assert "approval required" in denied["hint"]


def test_non_destructive_operation_needs_no_approval() -> None:
    pending = {"operation": "list_windows"}
    result = _guard(policy=_Policy(approval=False))(_state(pending_action=pending))

    assert result["guard_verdict"] == "allow"


# --- manual control & cancellation -------------------------------------------


def test_manual_control_blocks_desktop_input() -> None:
    node = _guard(policy=_Policy(user_control=True))
    pending = {"action": "left_click", "x": 100, "y": 200}

    result = node(_state(pending_action=pending))

    assert result["guard_verdict"] == "reject"
    assert "controls the desktop" in result["hint"]


def test_stopped_or_failed_task_stops_further_input() -> None:
    node = _guard()
    pending = {"action": "left_click", "x": 100, "y": 200}

    for status in ("stopped", "failed"):
        result = node(_state(pending_action=pending, status=status))
        assert result["guard_verdict"] == "stop"


def test_running_status_is_not_treated_as_stopped() -> None:
    node = _guard()
    pending = {"action": "left_click", "x": 100, "y": 200}

    for status in (None, "running"):
        result = node(_state(pending_action=pending, status=status))
        assert result["guard_verdict"] != "stop"


# --- shortcut focus availability --------------------------------------------------


def test_shortcut_available_for_focused_app_is_allowed() -> None:
    node = _guard()
    pending = {"action": "shortcut", "name": "terminal_clear"}

    result = node(_state(pending_action=pending, focused_app="terminal"))

    assert result["guard_verdict"] == "allow"


def test_shortcut_unavailable_for_focused_app_is_rejected() -> None:
    node = _guard()
    pending = {"action": "shortcut", "name": "browser_new_tab"}

    result = node(_state(pending_action=pending, focused_app="terminal"))

    assert result["guard_verdict"] == "reject"
    assert "not available for focus" in result["hint"]


def test_shortcut_unavailable_for_unknown_focus_is_rejected() -> None:
    node = _guard()
    pending = {"action": "shortcut", "name": "browser_new_tab"}

    result = node(_state(pending_action=pending, focused_app=None))

    assert result["guard_verdict"] == "reject"
    assert "not available for focus" in result["hint"]


def test_default_binding_shortcut_allowed_for_unbound_focus() -> None:
    # A shortcut with a default binding resolves for any focus, including none.
    node = _guard()
    pending = {"action": "shortcut", "name": "copy"}

    result = node(_state(pending_action=pending, focused_app=None))

    assert result["guard_verdict"] == "allow"


# --- repeat / recovery -------------------------------------------------------


def test_repeating_recent_failed_action_without_recovery_is_rejected() -> None:
    history = [{"decision": "action", "outcome": "failed", "action": {"operation": "open_url"}}]
    pending = {"operation": "open_url", "url": "https://example.com"}

    node = _guard()
    result = node(_state(pending_action=pending, history=history))

    assert result["guard_verdict"] == "reject"
    assert "repeat" in result["hint"]


def test_repeat_is_allowed_when_a_recovery_hint_is_present() -> None:
    history = [{"decision": "action", "outcome": "failed", "action": {"operation": "open_url"}}]
    pending = {"operation": "open_url", "url": "https://example.com"}

    node = _guard()
    result = node(_state(pending_action=pending, history=history, hint="retry the url"))

    assert result["guard_verdict"] == "allow"


def test_repeat_of_successful_action_is_not_blocked() -> None:
    history = [{"decision": "action", "outcome": "succeeded", "action": {"operation": "open_url"}}]
    pending = {"operation": "open_url", "url": "https://example.com"}

    result = _guard()(_state(pending_action=pending, history=history))

    assert result["guard_verdict"] == "allow"


# --- injectable parse --------------------------------------------------------


def test_injected_parse_is_used() -> None:
    seen: list[dict] = []

    def fake_parse(payload: dict):
        seen.append(payload)
        return object()

    node = make_guard(parse=fake_parse, policy=_Policy())
    pending = {"operation": "open_url", "url": "https://example.com"}

    result = node(_state(pending_action=pending))

    assert seen == [pending]
    assert result["guard_verdict"] == "allow"