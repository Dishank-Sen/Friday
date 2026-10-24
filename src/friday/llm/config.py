from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from .errors import LLMConfigError

DEFAULT_BASE_URL = "https://api.featherless.ai/v1"


@dataclass(frozen=True, slots=True)
class LLMSettings:
    provider: str
    model: str
    base_url: str
    api_key: str
    temperature: float
    timeout: float
    max_retries: int
    coordinate_grid: int

    @classmethod
    def from_env(cls) -> LLMSettings:
        load_dotenv()
        api_key = os.getenv("FEATHERLESS_API_KEY", "")
        model = os.getenv("FRIDAY_LLM_MODEL", "")
        if not api_key:
            raise LLMConfigError("FEATHERLESS_API_KEY is required")
        if not model:
            raise LLMConfigError("FRIDAY_LLM_MODEL is required")
        try:
            settings = cls(
                provider=os.getenv("FRIDAY_LLM_PROVIDER", "featherless"),
                model=model,
                base_url=os.getenv("FRIDAY_LLM_BASE_URL", DEFAULT_BASE_URL),
                api_key=api_key,
                temperature=float(os.getenv("FRIDAY_LLM_TEMPERATURE", "0")),
                timeout=float(os.getenv("FRIDAY_LLM_TIMEOUT", "60")),
                max_retries=int(os.getenv("FRIDAY_LLM_MAX_RETRIES", "2")),
                coordinate_grid=int(os.getenv("FRIDAY_COORDINATE_GRID", "1000")),
            )
        except ValueError as error:
            raise LLMConfigError("LLM numeric settings must be valid numbers") from error
        if settings.timeout <= 0 or settings.max_retries < 0 or settings.coordinate_grid <= 0:
            raise LLMConfigError(
                "LLM timeout and coordinate grid must be positive; retries cannot be negative"
            )
        return settings
