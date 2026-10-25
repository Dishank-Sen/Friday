from __future__ import annotations

from friday.harness.capabilities import ControlPolicy
from friday.harness.facts import FactLimits, _outcome, summarize_facts
from friday.harness.state import initial_state


def _state() -> dict:
    state = initial_state("open the terminal", 10)
    state["screenshot_path"] = "/tmp/shot.png"
    state["screen_size"] = (1280, 720)
    state["focused_app"] = "browser"
    state["windows"] = [
        {"id": "0x00000001", "title": "Chromium", "class_name": "Chromium", "active": True},
        {"id": "0x00000002", "title": "Terminal", "class_name": "Xfce4-terminal", "active": False},
    ]
    state["history"] = [{"decision": "action", "action": {"action": "key", "key": "ctrl+t"}}]
    state["last_result"] = {"ok": True, "detail": "tab opened"}
    state["step"] = 3
    state["retries"] = 1
    return state


def _long(length: int) -> str:
    return "x" * length


# --- normalization is consistent --------------------------------------------


def test_summarize_facts_normalizes_available_metadata() -> None:
    facts = summarize_facts(_state())

    assert facts.goal == "open the terminal"
    assert facts.screenshot == "/tmp/shot.png"
    assert facts.screen_size == (1280, 720)
    assert facts.focused_app == "browser"
    assert facts.windows[0]["id"] == "0x00000001"
    assert facts.windows[0]["title"] == "Chromium"
    assert facts.windows[0]["active"] is True
    assert facts.step == 3
    assert facts.max_steps == 10
    assert facts.steps_remaining == 7
    assert facts.retries == 1


# --- missing / unavailable desktop metadata ---------------------------------


def test_missing_facts_are_honest_none_and_bounded_remaining() -> None:
    facts = summarize_facts(initial_state("read the report", 7))

    assert facts.goal == "read the report"
    assert facts.screenshot is None
    assert facts.screen_size is None
    assert facts.focused_app is None
    assert facts.windows == ()
    assert facts.history == ()
    assert facts.last_result is None
    assert facts.hint is None
    assert facts.step == 0
    assert facts.steps_remaining == 7


def test_unavailable_desktop_metadata_are_not_fabricated() -> None:
    state = _state()
    state["screenshot_path"] = None
    state["screen_size"] = None
    state["focused_app"] = None

    facts = summarize_facts(state)

    assert facts.screenshot is None
    assert facts.screen_size is None
    assert facts.focused_app is None


def test_bad_window_fields_normalize_to_none_but_keep_the_entry() -> None:
    state = _state()
    state["windows"] = [
        {"id": "0x00000001", "title": "Chromium"},
        {"id": 42, "title": 123, "active": "yes"},
    ]

    facts = summarize_facts(state)

    assert len(facts.windows) == 2
    window = facts.windows[1]
    assert window["id"] is None
    assert window["title"] is None
    assert window["active"] is None


# --- histories and results are bounded --------------------------------------


def test_long_history_is_bounded_to_tail() -> None:
    state = _state()
    state["history"] = [
        {"decision": "action", "action": {"action": "key", "key": f"k{i}"}} for i in range(50)
    ]

    facts = summarize_facts(state, limits=FactLimits(max_history=10))

    assert len(facts.history) == 10
    # the most recent entries are kept, not the oldest
    assert facts.history[-1]["action"]["key"] == "k49"


def test_history_strings_are_truncated() -> None:
    state = _state()
    state["history"] = [{"decision": "action", "action": {"action": "type", "text": _long(500)}}]

    facts = summarize_facts(state, limits=FactLimits(max_string=20))

    entry = facts.history[0]
    assert len(entry["action"]["text"]) <= 21
    assert entry["action"]["text"].endswith("…")


# --- large operation results / error text are bounded -----------------------


def test_large_last_result_is_bounded_but_keep_success_flag() -> None:
    state = _state()
    state["last_result"] = {"ok": True, "detail": _long(500), "nested": {"secret": _long(500)}}

    facts = summarize_facts(state, limits=FactLimits(max_string=30))

    assert facts.last_result["ok"] is True
    assert len(facts.last_result["detail"]) <= 31
    # non-string nested content is dropped, not rendered unbounded
    assert facts.last_result["nested"] == {"secret": _long(500)}


def test_huge_error_text_is_truncated() -> None:
    state = _state()
    state["last_result"] = {"ok": False, "error": _long(2000)}

    facts = summarize_facts(state, limits=FactLimits(max_string=50))

    assert len(facts.last_result["error"]) <= 51
    assert facts.last_result["error"].endswith("…")


# --- honest outcome labeling ------------------------------------------------


def test_outcome_is_succeeded_only_when_result_says_ok() -> None:
    state = _state()
    state["last_result"] = {"ok": True, "detail": "tab opened"}
    assert _outcome(state) == "succeeded"


def test_outcome_failed_for_expected_execution_failure() -> None:
    state = _state()
    state["last_result"] = {"ok": False, "error": "connection refused"}
    assert _outcome(state) == "failed"


def test_outcome_rejected_for_guard_rejection() -> None:
    state = _state()
    state["guard_verdict"] = "reject"
    assert _outcome(state) == "rejected"


def test_proposed_not_executed_is_unverified_not_succeeded() -> None:
    state = initial_state("open the terminal", 10)
    state["pending_action"] = {"action": "open_url", "url": "https://example.com"}
    # a pending action with no result must not be labeled a success
    assert _outcome(state) == "unverified"


def test_unverified_executed_action_never_claimed_as_success() -> None:
    facts = summarize_facts(_state())
    by_result = summarize_facts({"pending_action": {"action": "key", "key": "ctrl+t"}})

    assert facts.outcome == "succeeded"
    assert by_result.outcome == "unverified"
    assert by_result.last_result is None


def test_outcome_none_for_no_attempt() -> None:
    state = _state()
    state["last_result"] = None
    state["guard_verdict"] = None
    state["pending_action"] = None
    assert _outcome(state) == "none"


def test_last_result_ok_flag_is_preserved_not_read_as_text() -> None:
    state = _state()
    state["last_result"] = {"ok": True, "detail": "ok"}
    bounded = summarize_facts(state).last_result
    assert bounded is not None
    assert bounded["ok"] is True and isinstance(bounded["ok"], bool)


# --- approval / user-control status -----------------------------------------


def test_policy_status_is_carried_through() -> None:
    facts = summarize_facts(_state(), policy=ControlPolicy(approval=True, user_control=True))

    assert facts.approval is True
    assert facts.user_control is True


def test_approval_is_not_assumed_when_policy_omitted() -> None:
    facts = summarize_facts(_state())

    assert facts.approval is False


# --- no side effects during fact collection ---------------------------------


def test_summarize_facts_is_side_effect_free() -> None:
    state = _state()
    state["last_result"] = {"ok": True, "detail": _long(500)}
    original_last_result = state["last_result"]["detail"]
    original_goal = state["goal"]

    facts = summarize_facts(state, limits=FactLimits(max_string=20))

    # the input state is untouched; bounding produced a separate copy
    assert state["last_result"]["detail"] == original_last_result
    assert state["goal"] == original_goal
    assert facts.last_result["detail"].endswith("…")