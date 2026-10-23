from __future__ import annotations

from io import BytesIO

import pytest
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from PIL import Image

from friday.graph.locate import LocateRunner
from friday.llm.config import LLMSettings
from friday.llm.errors import LLMParseError
from friday.llm.providers.featherless import FeatherlessLLM


def _png(width: int = 200, height: int = 100) -> bytes:
    image = Image.new("RGB", (width, height), "white")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _settings() -> LLMSettings:
    return LLMSettings(
        provider="featherless",
        model="test-model",
        base_url="https://example.invalid/v1",
        api_key="test-key",
        temperature=0,
        timeout=1,
        max_retries=2,
        coordinate_grid=1000,
    )


def test_graph_retries_a_bad_response_then_returns_pixels() -> None:
    chat = FakeMessagesListChatModel(
        responses=[AIMessage(content="not json"), AIMessage(content='{"x": 500, "y": 1000}')]
    )
    llm = FeatherlessLLM(_settings(), chat_model=chat)

    result = LocateRunner(llm, max_retries=2).locate(_png(), "open the terminal")

    assert result.normalized == (500, 1000)
    assert result.pixel == (100, 99)
    assert chat.i == 2


def test_graph_raises_after_parse_retries_are_exhausted() -> None:
    chat = FakeMessagesListChatModel(responses=[AIMessage(content="not json")])
    llm = FeatherlessLLM(_settings(), chat_model=chat)

    with pytest.raises(LLMParseError, match="not json"):
        LocateRunner(llm, max_retries=2).locate(_png(), "open the terminal")
