from .base import LLMResponse, VisionLLM
from .errors import LLMConfigError, LLMError, LLMParseError


def create_llm(*args: object, **kwargs: object) -> VisionLLM:
    from .providers.registry import create_llm as factory

    return factory(*args, **kwargs)

__all__ = [
    "LLMConfigError",
    "LLMError",
    "LLMParseError",
    "LLMResponse",
    "VisionLLM",
    "create_llm",
]
