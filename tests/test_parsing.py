import pytest

from friday.llm.errors import LLMParseError
from friday.vision.coords import parse_point


@pytest.mark.parametrize(
    ("text", "point"),
    [
        ('{"x": 12, "y": 34}', (12, 34)),
        ('  ```json\n{"x": 12, "y": 34}\n```  ', (12, 34)),
    ],
)
def test_parse_point_accepts_json_or_fence(text: str, point: tuple[int, int]) -> None:
    result = parse_point(text)

    assert (result.x, result.y) == point


@pytest.mark.parametrize(
    "text",
    [
        'Answer: {"x": 12, "y": 34}',
        '{"x": 12}',
        '{"x": 12.5, "y": 34}',
        "not json",
    ],
)
def test_parse_point_rejects_ambiguous_or_invalid_response(text: str) -> None:
    with pytest.raises(LLMParseError):
        parse_point(text)
