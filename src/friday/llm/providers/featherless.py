from __future__ import annotations

import logging
import time
from typing import Any

from langchain_openai import ChatOpenAI

from friday.llm.base import LLMResponse
from friday.llm.config import LLMSettings
from friday.llm.messages import build_message

LOGGER = logging.getLogger(__name__)


class FeatherlessLLM:
    def __init__(self, settings: LLMSettings, chat_model: Any | None = None) -> None:
        self._settings = settings
        self._model = chat_model
        if self._model is None:
            self._model = ChatOpenAI(
                model=settings.model,
                api_key=settings.api_key,
                base_url=settings.base_url,
                temperature=settings.temperature,
                timeout=settings.timeout,
                max_retries=settings.max_retries,
            )

    def invoke(self, prompt: str, images: list[bytes]) -> LLMResponse:
        started = time.monotonic()
        try:
            response = self._model.invoke([build_message(prompt, images)])
        finally:
            elapsed = time.monotonic() - started
            LOGGER.info(
                "Featherless model call completed: model=%s image_bytes=%d latency_seconds=%.3f",
                self._settings.model,
                sum(len(image) for image in images),
                elapsed,
            )
        content = response.content
        if not isinstance(content, str):
            raise TypeError("model response content was not text")
        return LLMResponse(text=content)
