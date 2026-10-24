"""Configuration defaults for the agent harness."""

from __future__ import annotations

from pathlib import Path

DEFAULT_RECURSION_LIMIT = 50

# Workspace root used to validate file-path operations. The guard considers paths
# that escape this root invalid regardless of what the model proposes.
WORKSPACE_ROOT = Path("/config/friday-workspace")

# Operations in these categories are treated as destructively sensitive and need
# explicit approval before the guard will allow them.
APPROVAL_REQUIRED_CATEGORIES = frozenset({"files", "processes", "windows"})

# Operation and action names build_context may offer, in one place as data so
# selection stays deterministic and auditable. The authoritative registries
# remain privileged; these sets only pick which names are surfaced. Core names
# are guard-allowable without approval; names in the higher-risk set are offered
# only when the injected policy permits the tier.
OBSERVE_OPERATIONS = frozenset({"list_windows", "active_window"})
CORE_OPERATIONS = frozenset(
    {"launch_app", "open_url", "focus_window", "wait_for_window"}
)
HIGHER_RISK_OPERATIONS = frozenset(
    {"close_window", "close_app", "delete_file", "write_file"}
)
OBSERVE_ACTIONS = frozenset({"screenshot", "cursor_position", "screen_size"})
CORE_ACTIONS = frozenset(
    {
        "left_click",
        "right_click",
        "double_click",
        "middle_click",
        "triple_click",
        "left_click_drag",
        "mouse_move",
        "scroll",
        "type",
        "key",
        "shortcut",
        "wait",
    }
)
