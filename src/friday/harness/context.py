"""Data contracts for the build_context node (no capability selection or rendering).

Only the typed structures live here. Capability *selection* against the current
state, prompt *rendering*, and graph wiring are deliberately not implemented in
this module; build_context composes them later from these contracts.

Design rules (see docs/harness.md):
- Capability descriptions are model-facing metadata, never executable
  implementations: the authoritative registries' callables (``builder``,
  ``argv`` construction, ``bindings``) are excluded from projections.
- Static agent instructions (the system prompt) stay separate from dynamic
  state.
- ``screen_size`` is internal bounds data; it is carried by ``PromptFacts`` for
  the decide node's coordinate checks but must never be rendered into a prompt.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from friday.harness.state import AgentState
from friday.operations.registry import (
    INPUT_OPERATIONS,
    OPERATIONS,
    OperationDefinition,
)
from friday.shortcuts.registry import SHORTCUTS, ShortcutDefinition

Decision = Literal["action", "done", "fail", "retry"]
Verdict = Literal["allow", "reject", "stop"]


@dataclass(frozen=True, slots=True)
class OperationCapability:
    """Model-facing projection of one OperationDefinition, minus its execution."""

    name: str
    category: str
    description: str
    argv: str
    timeout: float
    side_effects: str
    security: str


@dataclass(frozen=True, slots=True)
class ShortcutCapability:
    """Model-facing projection of one ShortcutDefinition, minus its bindings."""

    name: str
    context: str
    description: str
    expected_effect: str
    caveats: str
    risky: bool = False


@dataclass(frozen=True, slots=True)
class ActionCapability:
    """Model-facing projection of one desktop input/observation action.

    Drawn from ``INPUT_OPERATIONS`` (the execution-level ``Action`` catalog),
    kept separate from ``OperationCapability`` so raw input actions are never
    confused with system operations.
    """

    name: str
    category: str
    description: str
    argv: str


@dataclass(frozen=True, slots=True)
class CapabilityManifest:
    """The model-facing capability set available to one decision step.

    ``unavailable_note`` is an optional, model-facing note listing capabilities
    that exist but were withheld because the current policy does not permit the
    tier (so the model does not think the whole action class is missing).
    """

    operations: tuple[OperationCapability, ...] = ()
    shortcuts: tuple[ShortcutCapability, ...] = ()
    actions: tuple[ActionCapability, ...] = ()
    unavailable_note: str | None = None

    def __bool__(self) -> bool:
        return bool(self.operations or self.shortcuts or self.actions)


def operation_capability(definition: OperationDefinition) -> OperationCapability:
    """Project an authoritative operation definition into model-facing metadata."""
    return OperationCapability(
        name=definition.name,
        category=definition.category,
        description=definition.description,
        argv=definition.argv,
        timeout=definition.timeout,
        side_effects=definition.side_effects,
        security=definition.security,
    )


def shortcut_capability(definition: ShortcutDefinition) -> ShortcutCapability:
    """Project an authoritative shortcut definition into model-facing metadata."""
    return ShortcutCapability(
        name=definition.name,
        context=definition.context,
        description=definition.description,
        expected_effect=definition.expected_effect,
        caveats=definition.caveats,
        risky=definition.risky,
    )


def action_capability(name: str, category: str, argv: str, description: str) -> ActionCapability:
    """Project one INPUT_OPERATIONS entry into model-facing metadata."""
    return ActionCapability(name=name, category=category, description=description, argv=argv)


@dataclass(frozen=True, slots=True)
class ContextDependencies:
    """Injected, non-state inputs for building one context.

    ``system_prompt`` holds the static agent instructions, intentionally kept
    separate from the dynamic facts produced by ``PromptFacts.from_state``.
    """

    system_prompt: str = ""


SYSTEM_PROMPT = (
    "You are Friday, a desktop-operating agent. You act on an X11 desktop by "
    "choosing one validated action per step. Reason from the provided facts, "
    "history, and capabilities, and produce exactly the declared response shape."
)


@dataclass(frozen=True, slots=True)
class PromptFacts:
    """The dynamic, model-facing facts for one decision step.

    ``screen_size`` is carried here only as internal coordinate/bounds data for
    the decide node; per the harness contract it must never be rendered into a
    prompt.
    """

    goal: str | None
    screenshot_path: str | None
    screen_size: tuple[int, int] | None
    focused_app: str | None
    windows: tuple[dict, ...]
    history: tuple[dict, ...]
    last_result: dict | None
    hint: str | None
    step: int
    max_steps: int
    retries: int

    @classmethod
    def from_state(cls, state: AgentState) -> PromptFacts:
        """Extract the model-facing facts from a state snapshot."""
        return cls(
            goal=state.get("goal"),
            screenshot_path=state.get("screenshot_path"),
            screen_size=state.get("screen_size"),
            focused_app=state.get("focused_app"),
            windows=tuple(state.get("windows") or ()),
            history=tuple(state.get("history") or ()),
            last_result=state.get("last_result"),
            hint=state.get("hint"),
            step=state.get("step", 0),
            max_steps=state.get("max_steps", 0),
            retries=state.get("retries", 0),
        )

    @property
    def steps_remaining(self) -> int:
        return max(0, self.max_steps - self.step)


@dataclass(frozen=True, slots=True)
class ModelContext:
    """The complete structured input handed to the decision node."""

    facts: PromptFacts
    capabilities: CapabilityManifest

    @classmethod
    def from_manifest(
        cls,
        state: AgentState,
        capabilities: CapabilityManifest,
        *,
        operation_names: tuple[str, ...] = (),
        shortcut_names: tuple[str, ...] = (),
    ) -> ModelContext:
        """Assemble a context from a state snapshot and a capability selection.

        ``operation_names`` and ``shortcut_names`` select projections from the
        authoritative registries; empty names select nothing. Capability
        *selection policy* (e.g. filtered against ``focused_app``) belongs to
        build_context, not to this constructor.
        """
        operations = tuple(
            operation_capability(OPERATIONS[name]) for name in operation_names
        )
        shortcuts = tuple(shortcut_capability(SHORTCUTS[name]) for name in shortcut_names)
        return cls(
            facts=PromptFacts.from_state(state),
            capabilities=CapabilityManifest(operations=operations, shortcuts=shortcuts),
        )


@dataclass(frozen=True, slots=True)
class ResponseExpectation:
    """The declared shape the decision node must produce for one step."""

    decision: Decision | None = None
    pending_action: dict | None = None
    retried: bool = False


# Existing authoritative catalogs re-exported for composition without re-authoring.
ALL_OPERATIONS: dict[str, tuple[str, str, str]] = INPUT_OPERATIONS
ALL_SHORTCUTS: dict[str, ShortcutDefinition] = SHORTCUTS