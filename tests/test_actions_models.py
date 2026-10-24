import pytest
from pydantic import ValidationError

from friday.actions.models import (
    ACTION_ADAPTER,
    ActionResult,
    LeftClickAction,
    ScrollAction,
    parse_action,
)


def test_discriminated_union_parses_action() -> None:
    action = parse_action('{"action":"left_click","x":1,"y":2}')

    assert action == LeftClickAction(action="left_click", x=1, y=2)


@pytest.mark.parametrize(
    "payload",
    [
        {"action": "mouse_move", "x": 1.5, "y": 2},
        {"action": "scroll", "amount": 0},
        {"action": "scroll", "amount": 1, "x": 1},
        {"action": "scroll", "amount": 31},
        {"action": "type", "text": "x" * 2001},
        {"action": "hold_key", "key": "shift", "duration": 6},
        {"action": "wait", "seconds": 0},
        {"action": "zoom", "factor": 1.4, "x": 0, "y": 0},
    ],
)
def test_invalid_action_values_are_rejected(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ACTION_ADAPTER.validate_python(payload)


def test_action_result_round_trips_png_json() -> None:
    result = ActionResult(ok=True, image_png=b"\x89PNG\r\n\x1a\n")

    restored = ActionResult.model_validate_json(result.model_dump_json())

    assert restored.image_png == result.image_png


def test_scroll_accepts_complete_pointer_position() -> None:
    assert ScrollAction(action="scroll", amount=-1, x=2, y=3).x == 2
