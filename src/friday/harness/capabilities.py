"""Deterministic capability selection for the build_context node.

Selects the model-facing capability set from the authoritative registries
(``OPERATIONS``, ``INPUT_OPERATIONS``, ``SHORTCUTS``) based only on the focused
application, the injected policy, and the configured tiers — never on the goal
text. This is *not* a security boundary: it only shapes what the model may
attempt in one step, and the guard remains responsible for enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass

from friday.harness.config import (
    APPROVAL_REQUIRED_CATEGORIES,
    CORE_ACTIONS,
    CORE_OPERATIONS,
    HIGHER_RISK_OPERATIONS,
    OBSERVE_ACTIONS,
    OBSERVE_OPERATIONS,
)
from friday.harness.context import (
    CapabilityManifest,
    PromptFacts,
    action_capability,
    operation_capability,
    shortcut_capability,
)
from friday.operations.registry import INPUT_OPERATIONS, OPERATIONS
from friday.shortcuts.registry import SHORTCUTS, resolve_shortcut

# Focused-app categories that have a known shortcut-binding table. When the
# focused app is unknown, application-specific shortcuts are not assumed safe.
_KNOWN_FOCUS = frozenset({"browser", "terminal", "file_manager", "text_editor"})


@dataclass(frozen=True, slots=True)
class ControlPolicy:
    """Approval / user-control status for one step.

    ``approval`` is True when a human controller has approved the step (or no
    approval requirement is in force). ``user_control`` is True when the desktop
    is being driven by a human, so no input/action capability is surfaced.
    Kept concrete because the harness has no user-control state field yet;
    build_context supplies it.
    """

    approval: bool = True
    user_control: bool = False

    def records(self) -> bool:
        """Whether approval-sensitive capabilities may be surfaced."""
        return self.approval


def requires_approval(name: str, approval_categories: frozenset[str] | None = None) -> bool:
    """The one shared rule for whether an operation is approval-gated.

    Used by both the guard (to reject) and capability selection (to withhold):
    an operation needs explicit approval when its category is destructively
    sensitive (``APPROVAL_REQUIRED_CATEGORIES`` by default) *and* it has a side
    effect. A pure read such as ``list_windows`` or ``read_file`` is not gated.
    """
    definition = OPERATIONS.get(name)
    if definition is None:
        return False
    categories = (
        APPROVAL_REQUIRED_CATEGORIES if approval_categories is None else approval_categories
    )
    if definition.category not in categories:
        return False
    return definition.side_effects != "none"


def select_capabilities(
    *,
    facts: PromptFacts,
    policy: ControlPolicy | None = None,
) -> CapabilityManifest:
    """Select the capability set for one step, independent of the goal.

    Policies:
    - Core observation operations/actions are always offered unless the user
      controls the desktop (then only observe capabilities, no input).
    - Low-risk core operations are offered when their category is not
      approval-gated, or when approval is granted. Higher-risk operations are
      offered only when approval is granted, and a flagged-unavailable note is
      rendered otherwise — never the whole action class.
    - Shortcuts offered are exactly those ``resolve_shortcut`` accepts for the
      focused app (None means ``"other"``; an explicit-null binding never
      resolves), minus any ``risky`` shortcut when approval is not granted.

    Deterministic given the same input. Capability selection never overrides the
    guard: anything offered must be something the guard could allow under the
    same policy (see the consistency invariant in docs/harness.md).
    """
    focus = facts.focused_app or "other"
    policy = policy or ControlPolicy()

    if policy.user_control:
        return _bounded_manifest(
            set(OBSERVE_OPERATIONS), set(OBSERVE_ACTIONS), set(), unavailable=()
        )

    operation_names = set(OBSERVE_OPERATIONS)
    action_names = set(OBSERVE_ACTIONS)
    unavailable: tuple[str, ...] = ()

    for name in tuple(CORE_OPERATIONS):
        if requires_approval(name) and not policy.records():
            unavailable += (name,)
        else:
            operation_names.add(name)
    for name in tuple(HIGHER_RISK_OPERATIONS):
        if policy.records():
            operation_names.add(name)
        else:
            unavailable += (name,)
    action_names |= set(CORE_ACTIONS)

    shortcut_names = _shortcuts_for(focus, policy)
    return _bounded_manifest(
        operation_names, action_names, shortcut_names, unavailable=unavailable
    )


def _bounded_manifest(
    operation_names: set[str],
    action_names: set[str],
    shortcut_names: set[str],
    *,
    unavailable: tuple[str, ...],
) -> CapabilityManifest:
    operations = tuple(
        operation_capability(OPERATIONS[name]) for name in sorted(operation_names)
    )
    actions = tuple(
        action_capability(name, category, argv, description)
        for name, (category, argv, description) in sorted(INPUT_OPERATIONS.items())
        if name in action_names
    )
    shortcuts = tuple(
        shortcut_capability(SHORTCUTS[name]) for name in sorted(shortcut_names)
    )
    return CapabilityManifest(
        operations=operations,
        actions=actions,
        shortcuts=shortcuts,
        unavailable_note=_unavailable_note(unavailable),
    )


def _unavailable_note(unavailable: tuple[str, ...]) -> str | None:
    if not unavailable:
        return None
    names = ", ".join(sorted(unavailable))
    return (
        f"({names}) exist but need approval that is not currently available; "
        "do not propose them."
    )


def _shortcuts_for(focus: str, policy: ControlPolicy) -> set[str]:
    if focus not in _KNOWN_FOCUS:
        return set()
    available: set[str] = set()
    for name in SHORTCUTS:
        try:
            resolve_shortcut(name, focus)
        except ValueError:
            continue
        if policy.records() or not SHORTCUTS[name].risky:
            available.add(name)
    return available