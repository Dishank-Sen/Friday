from __future__ import annotations

import os
from io import BytesIO

import pytest
from PIL import Image

from friday.llm import create_llm
from friday.llm.config import LLMSettings


@pytest.mark.integration
def test_featherless_text_and_vision_requests() -> None:
    if os.environ.get("RUN_LLM_INTEGRATION") != "1":
        pytest.skip("set RUN_LLM_INTEGRATION=1 to run the real Featherless API test")
    llm = create_llm(LLMSettings.from_env())
    assert llm.invoke("Reply with exactly OK", []).text
    image = Image.new("RGB", (2, 2), "white")
    output = BytesIO()
    image.save(output, format="PNG")
    assert llm.invoke("Reply with exactly OK", [output.getvalue()]).text
