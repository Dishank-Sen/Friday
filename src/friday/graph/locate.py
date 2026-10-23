from __future__ import annotations

import logging
from dataclasses import dataclass
from importlib.resources import files
from io import BytesIO
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph
from PIL import Image, UnidentifiedImageError

from friday.llm.base import VisionLLM
from friday.llm.errors import LLMParseError
from friday.vision.coords import PointResponse, normalized_to_pixels, parse_point

from .state import LocateState

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LocateResult:
    normalized: tuple[int, int]
    pixel: tuple[int, int]
    raw_text: str
    image_size: tuple[int, int]


class LocateRunner:
    def __init__(self, llm: VisionLLM, *, coordinate_grid: int = 1000, max_retries: int = 2) -> None:
        if coordinate_grid <= 0:
            raise ValueError("coordinate_grid must be positive")
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        self._llm = llm
        self._coordinate_grid = coordinate_grid
        self._max_retries = max_retries
        self._graph = self._build_graph()

    def locate(self, png: bytes, instruction: str) -> LocateResult:
        width, height = _png_size(png)
        state = self._graph.invoke(
            {
                "instruction": instruction,
                "screenshot": png,
                "image_size": (width, height),
                "raw_model_output": "",
                "parsed_point": None,
                "pixel_point": None,
                "error": None,
                "attempts": 0,
            }
        )
        point = state["parsed_point"]
        pixel = state["pixel_point"]
        if point is None or pixel is None:
            raise LLMParseError(state["raw_model_output"])
        return LocateResult(
            normalized=(point.x, point.y),
            pixel=pixel,
            raw_text=state["raw_model_output"],
            image_size=state["image_size"],
        )

    def _build_graph(self) -> Any:
        graph = StateGraph(LocateState)
        graph.add_node("call_model", self._call_model)
        graph.add_node("parse", self._parse)
        graph.add_node("to_pixels", self._to_pixels)
        graph.add_edge(START, "call_model")
        graph.add_edge("call_model", "parse")
        graph.add_conditional_edges(
            "parse",
            self._after_parse,
            {"call_model": "call_model", "to_pixels": "to_pixels"},
        )
        graph.add_edge("to_pixels", END)
        return graph.compile()

    def _call_model(self, state: LocateState) -> dict[str, object]:
        attempt = state["attempts"] + 1
        LOGGER.info("locate model request attempt=%d image_bytes=%d", attempt, len(state["screenshot"]))
        prompt = _load_prompt().format(
            instruction=state["instruction"], grid=self._coordinate_grid
        )
        response = self._llm.invoke(prompt, [state["screenshot"]])
        return {"raw_model_output": response.text, "attempts": attempt, "error": None}

    def _parse(self, state: LocateState) -> dict[str, object]:
        try:
            point = parse_point(state["raw_model_output"])
        except LLMParseError as error:
            return {"parsed_point": None, "error": str(error)}
        return {"parsed_point": point, "error": None}

    def _to_pixels(self, state: LocateState) -> dict[str, object]:
        point = state["parsed_point"]
        if point is None:
            raise LLMParseError(state["raw_model_output"])
        width, height = state["image_size"]
        return {"pixel_point": normalized_to_pixels(point, width, height, self._coordinate_grid)}

    def _after_parse(self, state: LocateState) -> Literal["call_model", "to_pixels"]:
        if state["parsed_point"] is not None:
            return "to_pixels"
        if state["attempts"] <= self._max_retries:
            return "call_model"
        raise LLMParseError(f"could not parse model output after {state['attempts']} attempts: {state['raw_model_output']}")


def locate(llm: VisionLLM, png: bytes, instruction: str) -> LocateResult:
    return LocateRunner(llm).locate(png, instruction)


def _load_prompt() -> str:
    return files("friday.prompts").joinpath("locate.txt").read_text(encoding="utf-8")


def _png_size(png: bytes) -> tuple[int, int]:
    try:
        with Image.open(BytesIO(png)) as image:
            if image.format != "PNG":
                raise ValueError("locate requires PNG screenshot bytes")
            return image.size
    except UnidentifiedImageError as error:
        raise ValueError("locate requires valid PNG screenshot bytes") from error
