from __future__ import annotations

from typing import TypedDict

from friday.vision.coords import PointResponse


class LocateState(TypedDict):
    instruction: str
    screenshot: bytes
    image_size: tuple[int, int]
    raw_model_output: str
    parsed_point: PointResponse | None
    pixel_point: tuple[int, int] | None
    error: str | None
    attempts: int
