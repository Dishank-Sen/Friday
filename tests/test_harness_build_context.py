from __future__ import annotations

from friday.harness.capabilities import ControlPolicy
from friday.harness.context import CapabilityManifest, OperationCapability
from friday.harness.facts import NormalizedFacts
from friday.harness.nodes.build_context import make_build_context
from friday.harness.state import initial_state

_GOAL = "open a web page"


def _state(**overrides) -> dict:
    state = initial_state(_GOAL, 10)
    state["screenshot_path"] = "/tmp/shot.png"
    state["screen_size"] = (1280, 720)
    state["focused_app"] = "browser"
    state["windows"] = [{"id": "0x00000001", "title": "Chromium", "active": True}]
    state["history"] = [{"decision": "action", "action": {"action": "key", "key": "ctrl+t"}}]
    state["last_result"] = {"ok": True, "detail": "tab opened"}
    state["step"] = 3
    state["hint"] = "try again"
    state["retries"] = 1
    state.update(overrides)
    return state


def _manifest() -> CapabilityManifest:
    return CapabilityManifest(
        operations=(
            OperationCapability(
                "open_url", "launch", "Open a URL", "chromium <url>", 10.0, "opens a tab", "safe"
            ),
        )
    )


def _policy(approval: bool = True, user_control: bool = False):
    return ControlPolicy(approval=approval, user_control=user_control)


class _PolicyProvider:
    def __init__(self, approval: bool = True, user_control: bool = False) -> None:
        self._policy = _policy(approval, user_control)

    def policy(self, state) -> ControlPolicy:  # noqa: ANN001
        return self._policy


# --- successful context construction ----------------------------------------


def test_default_dependencies_build_a_prompt_and_clear_hint() -> None:
    node = make_build_context(policy=_PolicyProvider())

    update = node(_state())

    assert set(update) == {"prompt", "hint"}
    prompt = update["prompt"]
    assert prompt is not None
    assert _GOAL in prompt  # rendered goal
    assert "open_url" in prompt  # selected capability rendered
    # hint was consumed and cleared
    assert update["hint"] is None
    assert "try again" in prompt  # folded into the prompt


def test_injected_dependencies_are_used_exactly_once() -> None:
    calls: dict[str, list] = {"summary": [], "select": [], "render": []}

    def summarizer(state, policy):
        calls["summary"].append(policy)
        return NormalizedFacts(
            goal=state.get("goal"),
            screenshot=None,
            screen_size=None,
            focused_app=None,
            windows=(),
            history=(),
            last_result=None,
            outcome="none",
            hint=None,
            step=0,
            max_steps=10,
            steps_remaining=10,
            retries=0,
            approval=policy.approval,
            user_control=policy.user_control,
        )

    def selector(facts, policy):
        calls["select"].append((facts, policy))
        return _manifest()

    def renderer(facts, manifest):
        calls["render"].append((facts, manifest))
        return "RENDERED"

    node = make_build_context(summarizer=summarizer, selector=selector, renderer=renderer)

    update = node(_state())

    assert update == {"prompt": "RENDERED", "hint": None}
    assert len(calls["summary"]) == 1
    assert len(calls["select"]) == 1
    assert len(calls["render"]) == 1
    # the same policy flows through all three
    assert calls["select"][0][1] == calls["summary"][0]


# --- missing metadata (no fabrication) --------------------------------------


def test_missing_metadata_produces_a_prompt_without_fabrication() -> None:
    node = make_build_context(policy=_PolicyProvider())

    update = node(initial_state(_GOAL, 10))

    prompt = update["prompt"]
    assert prompt is not None
    assert "Focused application: unknown" in prompt
    assert "Windows: []" in prompt
    assert "unknown" in prompt


# --- dependency failure ------------------------------------------------------


def test_summarizer_failure_returns_safe_fallback() -> None:
    def summarizer(state, policy):
        raise RuntimeError("boom")

    node = make_build_context(summarizer=summarizer, policy=_PolicyProvider())

    assert node(_state()) == {"prompt": None, "hint": None}


def test_selector_failure_returns_safe_fallback() -> None:
    def summarizer(state, policy):
        return NormalizedFacts(
            goal=_GOAL, screenshot=None, screen_size=None, focused_app=None, windows=(),
            history=(), last_result=None, outcome="none", hint=None, step=0, max_steps=10,
            steps_remaining=10, retries=0, approval=True, user_control=False,
        )

    def selector(facts, policy):
        raise RuntimeError("boom")

    node = make_build_context(summarizer=summarizer, selector=selector)

    assert node(_state()) == {"prompt": None, "hint": None}


# --- manual control ----------------------------------------------------------


def test_manual_control_is_surfaced_through_injected_policy() -> None:
    seen: list[ControlPolicy] = []

    def summarizer(state, policy):
        seen.append(policy)
        return NormalizedFacts(
            goal=_GOAL, screenshot=None, screen_size=None, focused_app=None, windows=(),
            history=(), last_result=None, outcome="none", hint=None, step=0, max_steps=10,
            steps_remaining=10, retries=0, approval=policy.approval,
            user_control=policy.user_control,
        )

    def renderer(facts, manifest):
        return f"USER_CONTROL={facts.user_control}"

    node = make_build_context(
        summarizer=summarizer, renderer=renderer, policy=_PolicyProvider(user_control=True)
    )

    update = node(_state())

    # the injected policy drives both facts and the safe selection
    assert update["prompt"] == "USER_CONTROL=True"
    assert seen[0].user_control is True


def test_build_prompt_under_user_control_never_offers_input_capabilities() -> None:
    node = make_build_context(policy=_PolicyProvider(user_control=True))

    prompt = node(_state())["prompt"]
    assert prompt is not None
    # observe-only set offers reads but never inputs/operations that mutate
    assert "left_click" not in prompt
    assert "open_terminal_in" not in prompt


# --- budget exhaustion -------------------------------------------------------


def test_budget_exhaustion_marks_no_remaining_steps() -> None:
    node = make_build_context(policy=_PolicyProvider())

    update = node(_state(step=10, max_steps=10))

    prompt = update["prompt"]
    assert prompt is not None
    assert "steps remaining: 0" in prompt


# --- no execution ------------------------------------------------------------


def test_node_returns_only_prompt_and_hint_never_executes() -> None:
    node = make_build_context(policy=_PolicyProvider())

    update = node(_state(step=1, max_steps=3))

    assert set(update) == {"prompt", "hint"}
    # no side-effect state fields (no pending_action, no status change)
    assert "pending_action" not in update
    assert "status" not in update