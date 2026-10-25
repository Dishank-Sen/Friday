MAX_DRAG_STEPS = 10
MAX_HOLD_SECONDS = 5.0
MAX_MOUSE_MOVE_SECONDS = 2.0
MAX_SCROLL_AMOUNT = 30
MAX_TEXT_LENGTH = 2000
MAX_WAIT_SECONDS = 10.0
MIN_ZOOM_FACTOR = 1.5
MAX_ZOOM_FACTOR = 4.0

# Baseline allowed duration for one desktop action request. Individual actions
# may need more; ``timeout_for`` returns the budget for a specific action.
DEFAULT_EXECUTION_TIMEOUT = 15.0

# Margins and per-unit typing delay used to derive an action's execution timeout.
_TIMEOUT_MARGIN = 3.0
_TYPE_CHAR_SECONDS = 0.02


def timeout_for(action: object) -> float:
    """Return a safe execution timeout for one action or operation.

    The budget must exceed the action's own maximum duration so a long `wait`,
    `hold_key`, `mouse_move`, or big `type` is not killed early. Operates purely
    on the action's fields (no registry import), so it stays in config.
    """
    action_name = getattr(action, "action", None) or getattr(action, "operation", None)

    if action_name == "wait":
        return getattr(action, "seconds", 0.0) + _TIMEOUT_MARGIN
    if action_name == "hold_key":
        return getattr(action, "duration", 0.0) + _TIMEOUT_MARGIN
    if action_name == "mouse_move":
        return getattr(action, "duration", 0.0) + _TIMEOUT_MARGIN
    if action_name == "type":
        return len(getattr(action, "text", "")) * _TYPE_CHAR_SECONDS + _TIMEOUT_MARGIN
    if action_name == "wait_for_window":
        return getattr(action, "timeout", 5.0) + _TIMEOUT_MARGIN
    return DEFAULT_EXECUTION_TIMEOUT
