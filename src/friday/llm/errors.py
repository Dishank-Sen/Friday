class LLMError(RuntimeError):
    """Base class for LLM failures."""


class LLMConfigError(LLMError):
    """LLM configuration is missing or invalid."""


class LLMParseError(LLMError):
    """The model response did not contain a valid coordinate."""
