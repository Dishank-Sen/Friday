from __future__ import annotations

from friday.harness.capabilities import ControlPolicy, requires_approval, select_capabilities
from friday.harness.context import CapabilityManifest, PromptFacts
from friday.harness.nodes.guard import make_guard
from friday.harness.state import initial_state
from friday.operations.registry import INPUT_OPERATIONS, OPERATIONS
from friday.shortcuts.registry import SHORTCUTS


def _facts(goal: str = "open a browser", focused_app: str | None = "browser") -> PromptFacts:
    state = initial_state(goal, 10)
    state["focused_app"] = focused_app
    return PromptFacts.from_state(state)


def _names(manifest: CapabilityManifest) -> set[str]:
    names = {operation.name for operation in manifest.operations}
    names |= {action.name for action in manifest.actions}
    names |= {shortcut.name for shortcut in manifest.shortcuts}
    return names


def _ops(manifest: CapabilityManifest) -> set[str]:
    return {operation.name for operation in manifest.operations}


def _shortcuts(manifest: CapabilityManifest) -> set[str]:
    return {shortcut.name for shortcut in manifest.shortcuts}


def _policy(approval: bool = False, user_control: bool = False) -> ControlPolicy:
    return ControlPolicy(approval=approval, user_control=user_control)


# --- every returned capability exists in an authoritative registry ----------


def test_requires_approval_marks_sensitive_side_effect_operations() -> None:
    # the shared risk source: selection and guard both use this predicate
    assert not requires_approval("open_url")
    assert not requires_approval("list_windows")
    assert requires_approval("write_file")
    assert requires_approval("delete_file")
    assert requires_approval("close_window")
    assert requires_approval("close_app")


def test_returned_capabilities_exist_in_authoritative_registries() -> None:
    manifest = select_capabilities(facts=_facts(), policy=_policy())
    for operation in manifest.operations:
        assert operation.name in OPERATIONS
    for action in manifest.actions:
        assert action.name in INPUT_OPERATIONS
    for shortcut in manifest.shortcuts:
        assert shortcut.name in SHORTCUTS


def test_capability_metadata_comes_from_registry_not_a_second_source() -> None:
    manifest = select_capabilities(facts=_facts(), policy=_policy())

    open_url = next(o for o in manifest.operations if o.name == "open_url")
    assert open_url.description == OPERATIONS["open_url"].description
    assert open_url.timeout == OPERATIONS["open_url"].timeout
    assert open_url.side_effects == OPERATIONS["open_url"].side_effects

    new_tab = next(s for s in manifest.shortcuts if s.name == "browser_new_tab")
    assert new_tab.description == SHORTCUTS["browser_new_tab"].description
    assert new_tab.expected_effect == SHORTCUTS["browser_new_tab"].expected_effect


# --- regression: a normal task can succeed under the default policy ----------


def test_google_goal_offers_open_url_and_input_actions_under_default_policy() -> None:
    manifest = select_capabilities(
        facts=_facts("open https://www.google.com in a browser", focused_app="browser"),
        policy=_policy(approval=False),
    )

    assert "open_url" in _ops(manifest)
    assert "launch_app" in _ops(manifest)
    # input actions offered without any approval
    for action in ("key", "type", "left_click", "right_click", "mouse_move", "wait"):
        assert action in {a.name for a in manifest.actions}
    # the browser shortcuts that resolve for the focused app are offered
    assert "browser_new_tab" in _shortcuts(manifest)


# --- goal independence ------------------------------------------------------


def test_capability_list_is_independent_of_goal_text() -> None:
    a = select_capabilities(
        facts=_facts("open https://www.google.com in a browser", focused_app="browser"),
        policy=_policy(),
    )
    b = select_capabilities(
        facts=_facts("read the quarterly budget spreadsheet please", focused_app="browser"),
        policy=_policy(),
    )

    assert _names(a) == _names(b)
    assert a.operations == b.operations
    assert a.actions == b.actions
    assert a.shortcuts == b.shortcuts


def test_goal_text_never_changes_capabilities_for_terminal_focus() -> None:
    goal_a = select_capabilities(
        facts=_facts("clear the terminal output", focused_app="terminal"),
        policy=_policy(),
    )
    goal_b = select_capabilities(
        facts=_facts("nothing at all here", focused_app="terminal"),
        policy=_policy(),
    )

    assert _names(goal_a) == _names(goal_b)


# --- focused_app changes the shortcut set -----------------------------------


def test_focused_app_changes_the_shortcut_set() -> None:
    terminal = select_capabilities(facts=_facts(focused_app="terminal"), policy=_policy())
    browser = select_capabilities(facts=_facts(focused_app="browser"), policy=_policy())

    assert "copy" in _shortcuts(terminal)  # has a terminal binding
    assert "browser_new_tab" not in _shortcuts(terminal)
    assert "browser_new_tab" in _shortcuts(browser)
    assert "terminal_clear" not in _shortcuts(browser)


def test_explicit_null_binding_is_never_offered() -> None:
    # `undo`, `redo`, `save`, `cut` have an explicit null binding for terminal,
    # so resolve_shortcut raises and they must not be offered there.
    terminal = select_capabilities(facts=_facts(focused_app="terminal"), policy=_policy())

    for name in ("cut", "undo", "redo", "save"):
        assert name not in _shortcuts(terminal)


def test_unknown_focused_app_exposes_no_application_shortcuts() -> None:
    manifest = select_capabilities(facts=_facts(focused_app=None), policy=_policy())

    assert _shortcuts(manifest) == set()
    # observe + low-risk operations remain available
    assert "list_windows" in _ops(manifest)
    assert "open_url" in _ops(manifest)


# --- risk tiers -------------------------------------------------------------


def test_higher_risk_operations_absent_under_default_policy() -> None:
    manifest = select_capabilities(facts=_facts(), policy=_policy(approval=False))

    assert "delete_file" not in _ops(manifest)
    assert "write_file" not in _ops(manifest)
    assert "close_window" not in _ops(manifest)
    assert "close_app" not in _ops(manifest)


def test_higher_risk_operations_present_under_granting_policy() -> None:
    manifest = select_capabilities(facts=_facts(), policy=_policy(approval=True))

    assert "delete_file" in _ops(manifest)
    assert "write_file" in _ops(manifest)
    assert "close_window" in _ops(manifest)
    assert "close_app" in _ops(manifest)


def test_gated_operation_note_mentions_withheld_names_but_keeps_class() -> None:
    manifest = select_capabilities(facts=_facts(), policy=_policy(approval=False))

    assert manifest.unavailable_note is not None
    # the whole action class is not hidden: low-risk operations still present
    assert "open_url" in _ops(manifest)
    assert "launch_app" in _ops(manifest)
    for name in ("delete_file", "write_file", "close_window", "close_app"):
        assert name in manifest.unavailable_note


def test_granting_policy_has_no_unavailable_note() -> None:
    manifest = select_capabilities(facts=_facts(), policy=_policy(approval=True))

    assert manifest.unavailable_note is None


def test_risky_shortcut_withheld_without_approval_but_granted_with_it() -> None:
    # `window_close` has a default binding (resolves for any focus) and is risky.
    denied = select_capabilities(
        facts=_facts(focused_app="browser"), policy=_policy(approval=False)
    )
    granted = select_capabilities(
        facts=_facts(focused_app="browser"), policy=_policy(approval=True)
    )

    assert "window_close" not in _shortcuts(denied)
    assert "window_close" in _shortcuts(granted)


# --- non-risky shortcuts survive without approval ---------------------------


def test_non_risky_shortcut_offered_without_approval() -> None:
    manifest = select_capabilities(
        facts=_facts(focused_app="browser"), policy=_policy(approval=False)
    )

    # window_switch is not flagged risky and resolves for any focus
    assert "window_switch" in _shortcuts(manifest)


# --- manual control ---------------------------------------------------------


def test_user_control_exposes_only_observe_capabilities() -> None:
    manifest = select_capabilities(
        facts=_facts(focused_app="browser"), policy=_policy(user_control=True)
    )

    assert _ops(manifest) == {"list_windows", "active_window"}
    assert {action.name for action in manifest.actions} == {
        "cursor_position",
        "screen_size",
        "screenshot",
    }
    assert _shortcuts(manifest) == set()
    assert "open_url" not in _ops(manifest)


# --- deterministic ----------------------------------------------------------


def test_selection_is_deterministic() -> None:
    facts = _facts(focused_app="browser")
    first = select_capabilities(facts=facts, policy=_policy())
    second = select_capabilities(facts=facts, policy=_policy())

    assert _names(first) == _names(second)
    assert first.operations == second.operations
    assert first.unavailable_note == second.unavailable_note


# --- capability section stays small across focus values and policies ---------


def test_capability_section_stays_compact_across_focus_and_policy() -> None:
    from friday.harness.facts import summarize_facts
    from friday.harness.render import render_prompt

    for focus in ("browser", "terminal", "file_manager", "text_editor", "other", None):
        for approval in (False, True):
            state = initial_state("x", 10)
            state["focused_app"] = focus
            state["screen_size"] = (1280, 720)
            state["step"] = 1
            state["retries"] = 1
            policy = _policy(approval=approval)
            manifest = select_capabilities(facts=_facts(focused_app=focus), policy=policy)
            prompt = render_prompt(summarize_facts(state, policy=policy), manifest)

            start = prompt.index("## Available operations")
            end = prompt.index("## Response schema")
            section = prompt[start:end]
            # keep the whole capability section well under the existing hard cap
            assert len(section) < 10000, f"focus={focus} approval={approval}: {len(section)}"


# --- consistency invariant: offered ops/shortcuts pass guard -----------------


class _GuardPolicy:
    def __init__(self, approval: bool) -> None:
        self._policy = _policy(approval=approval)

    def policy(self, state):
        return self._policy


_OPERATION_PAYLOAD: dict[str, dict] = {
    "open_url": {"operation": "open_url", "url": "https://example.com"},
    "launch_app": {"operation": "launch_app", "app": "browser"},
    "focus_window": {"operation": "focus_window", "window_id": "0x00000001"},
    "wait_for_window": {"operation": "wait_for_window", "title": "something"},
    "list_windows": {"operation": "list_windows"},
    "active_window": {"operation": "active_window"},
    "close_window": {"operation": "close_window", "window_id": "0x00000001"},
    "close_app": {"operation": "close_app", "pid": 123},
    "delete_file": {"operation": "delete_file", "path": "notes.txt"},
    "write_file": {"operation": "write_file", "path": "notes.txt", "content": "x"},
}


def _guard_state(focused_app: str, approval: bool) -> dict:
    state = initial_state("x", 10)
    state["focused_app"] = focused_app
    state["screen_size"] = (1280, 720)
    state["step"] = 1
    state["retries"] = 2
    state["history"] = []
    return state


def test_every_offered_operation_passes_guard_under_the_same_policy() -> None:
    for approval in (False, True):
        for focus in ("browser", "terminal", None):
            manifest = select_capabilities(
                facts=_facts(focused_app=focus), policy=_policy(approval=approval)
            )
            guard = make_guard(policy=_GuardPolicy(approval))
            for op in manifest.operations:
                payload = _OPERATION_PAYLOAD.get(op.name)
                if payload is None:
                    continue
                state = _guard_state(focus or "other", approval)
                state["pending_action"] = payload
                result = guard(state)
                assert result["guard_verdict"] == "allow", (
                    f"{op.name} offered under approval={approval} focus={focus} "
                    f"but guard returned {result['guard_verdict']}: {result['hint']}"
                )


def test_every_offered_shortcut_passes_guard_under_the_same_policy() -> None:
    for approval in (False, True):
        for focus in ("browser", "terminal"):
            manifest = select_capabilities(
                facts=_facts(focused_app=focus), policy=_policy(approval=approval)
            )
            guard = make_guard(policy=_GuardPolicy(approval))
            for shortcut in manifest.shortcuts:
                state = _guard_state(focus, approval)
                state["pending_action"] = {
                    "action": "shortcut",
                    "name": shortcut.name,
                }
                result = guard(state)
                assert result["guard_verdict"] == "allow", (
                    f"{shortcut.name} offered under approval={approval} focus={focus} "
                    f"but guard returned {result['guard_verdict']}: {result['hint']}"
                )