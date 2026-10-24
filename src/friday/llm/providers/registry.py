from __future__ import annotations

from friday.llm.base import VisionLLM
from friday.llm.config import LLMSettings
from friday.llm.errors import LLMConfigError

from .featherless import FeatherlessLLM

PROVIDERS: dict[str, type[VisionLLM]] = {"featherless": FeatherlessLLM}


def create_llm(settings: LLMSettings) -> VisionLLM:
    try:
        provider = PROVIDERS[settings.provider.lower()]
    except KeyError as error:
        supported = ", ".join(sorted(PROVIDERS))
        raise LLMConfigError(
            f"unknown LLM provider {settings.provider!r}; supported: {supported}"
        ) from error
    return provider(settings)
