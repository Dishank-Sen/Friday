from __future__ import annotations

from dataclasses import fields

from friday.harness.context import (
    SYSTEM_PROMPT,
    CapabilityManifest,
    ContextDependencies,
    ModelContext,
    OperationCapability,
    PromptFacts,
    ResponseExpectation,
    ShortcutCapability,
)
from friday.harness.state import initial_state
from friday.operations.registry import OPERATIONS
from friday.shortcuts.registry import SHORTCUTS

_GOAL = "open the terminal"


def _state() -> dict:
    state = initial_state(_GOAL, 10)
    state["screen_size"] = (1280, 720)
    state["focused_app"] = "browser"
    state["windows"] = [
        {"id": "0x00000001", "title": "Chromium", "class_name": "Chromium", "active": True},
        {"id": "0x00000002", "title": "Terminal", "class_name": "Xfce4-terminal", "active": False},
    ]
    state["history"] = [{"decision": "action", "action": {"action": "key", "key": "ctrl+t"}}]
    state["last_result"] = {"ok": True, "detail": "tab opened"}
    state["hint"] = "tab switch succeeded"
    state["step"] = 3
    state["retries"] = 1
    return state


# --- CapabilityManifest ----------------------------------------------------


def test_operation_capability_projects_model_facing_metadata_only() -> None:
    definition = OPERATIONS["open_url"]

    capability = OperationCapability(
        name=definition.name,
        category=definition.category,
        description=definition.description,
        argv=definition.argv,
        timeout=definition.timeout,
        side_effects=definition.side_effects,
        security=definition.security,
    )

    assert capability.name == "open_url"
    assert capability.category == "launch"
    assert capability.argv == definition.argv
    assert capability.security == "validated before execution"
    assert capability.__class__.__name__ == "OperationCapability"


def test_operation_capability_is_frozen_and_has_no_execution_field() -> None:
    capability = OperationCapability(
        name="open_url",
        category="launch",
        description="opens URL",
        argv="chromium <url>",
        timeout=10.0,
        side_effects="opens URL",
        security="validated before execution",
    )

    assert not hasattr(capability, "builder")
    assert fields(OperationCapability)[0].name == "name"


def test_shortcut_capability_projects_metadata_without_bindings() -> None:
    definition = SHORTCUTS["copy"]

    capability = ShortcutCapability(
        name=definition.name,
        context=definition.context,
        description=definition.description,
        expected_effect=definition.expected_effect,
        caveats=definition.caveats,
        risky=definition.risky,
    )

    assert capability.name == "copy"
    assert capability.context == "text"
    assert not hasattr(capability, "bindings")


def test_capability_manifest_truthiness() -> None:
    assert not CapabilityManifest()
    assert CapabilityManifest(
        operations=(
            OperationCapability(
                "open_url", "launch", "opens URL", "chromium <url>", 10.0, "opens URL", "validated"
            ),
        )
    )
    assert CapabilityManifest(
        shortcuts=(
            ShortcutCapability("copy", "text", "Copy", "clipboard", "", False),
        )
    )


# --- PromptFacts -----------------------------------------------------------


def test_prompt_facts_from_state() -> None:
    facts = PromptFacts.from_state(_state())

    assert facts.goal == _GOAL
    assert facts.screen_size == (1280, 720)
    assert facts.focused_app == "browser"
    assert facts.windows[0]["title"] == "Chromium"
    assert facts.history[0]["decision"] == "action"
    assert facts.last_result == {"ok": True, "detail": "tab opened"}
    assert facts.hint == "tab switch succeeded"
    assert facts.step == 3
    assert facts.max_steps == 10
    assert facts.retries == 1
    assert facts.screenshot_path is None


def test_prompt_facts_from_empty_state() -> None:
    facts = PromptFacts.from_state(initial_state(_GOAL, 7))

    assert facts.goal == _GOAL
    assert facts.windows == ()
    assert facts.history == ()
    assert facts.last_result is None
    assert facts.screen_size is None
    assert facts.step == 0
    assert facts.max_steps == 7
    assert facts.retries == 0


def test_steps_remaining_bounds() -> None:
    state = initial_state(_GOAL, 10)
    state["step"] = 4
    assert PromptFacts.from_state(state).steps_remaining == 6

    state["step"] = 99
    assert PromptFacts.from_state(state).steps_remaining == 0


# --- ContextDependencies ---------------------------------------------------


def test_system_prompt_stays_separate_from_dynamic_state() -> None:
    dependencies = ContextDependencies(system_prompt=SYSTEM_PROMPT)

    assert "Friday" in dependencies.system_prompt
    assert "You act on an X11 desktop" in dependencies.system_prompt
    # Dynamic facts never leak into the static instructions.
    assert _GOAL not in dependencies.system_prompt


def test_system_prompt_defaults_to_empty() -> None:
    assert ContextDependencies().system_prompt == ""


# --- ModelContext ----------------------------------------------------------


def test_model_context_from_manifest_selects_capabilities() -> None:
    context = ModelContext.from_manifest(
        _state(),
        CapabilityManifest(),
        operation_names=("open_url", "list_windows"),
        shortcut_names=("copy", "browser_new_tab"),
    )

    names = {capability.name for capability in context.capabilities.operations}
    assert names == {"open_url", "list_windows"}
    shortcut_names = {capability.name for capability in context.capabilities.shortcuts}
    assert shortcut_names == {"copy", "browser_new_tab"}
    assert not hasattr(context.capabilities.operations[0], "builder")
    assert context.facts.goal == _GOAL
    assert context.facts.screen_size == (1280, 720)


def test_model_context_from_manifest_empty_selection() -> None:
    context = ModelContext.from_manifest(_state(), CapabilityManifest())

    assert context.capabilities.operations == ()
    assert context.capabilities.shortcuts == ()
    assert not context.capabilities


# --- ResponseExpectation ---------------------------------------------------


def test_response_expectation_declares_decision_pending_action_retried() -> None:
    expectation = ResponseExpectation(decision="action", pending_action={"action": "key"})

    assert expectation.decision == "action"
    assert expectation.pending_action == {"action": "key"}
    assert expectation.retried is False