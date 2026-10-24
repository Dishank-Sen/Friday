from __future__ import annotations

import json

from pydantic import BaseModel, StrictInt, ValidationError

from friday.llm.errors import LLMParseError


class PointResponse(BaseModel):
    x: StrictInt
    y: StrictInt


def parse_point(text: str) -> PointResponse:
    payload = _remove_code_fence(text.strip())
    try:
        return PointResponse.model_validate(json.loads(payload))
    except (ValidationError, json.JSONDecodeError) as error:
        raise LLMParseError("model response must be JSON with integer x and y fields") from error


def to_pixel(v: float, size: int, grid: int = 1000) -> int:
    if not 0 <= v <= grid:
        raise ValueError(f"normalized coordinate must be between 0 and {grid}")
    if size <= 0:
        raise ValueError("image size must be positive")
    if grid <= 0:
        raise ValueError("coordinate grid must be positive")
    return min(round(v / grid * size), size - 1)


def normalized_to_pixels(
    point: PointResponse, width: int, height: int, grid: int = 1000
) -> tuple[int, int]:
    return to_pixel(point.x, width, grid), to_pixel(point.y, height, grid)


def _remove_code_fence(text: str) -> str:
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if len(lines) < 3 or lines[-1].strip() != "```":
        return text
    language = lines[0].strip()[3:].strip()
    if language not in {"", "json"}:
        return text
    return "\n".join(lines[1:-1]).strip()
