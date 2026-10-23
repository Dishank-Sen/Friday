from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class LLMResponse:
    text: str


class VisionLLM(Protocol):
    def invoke(self, prompt: str, images: list[bytes]) -> LLMResponse: ...
