from __future__ import annotations

from friday.harness.nodes.decide import make_decide
from friday.harness.state import initial_state
from friday.llm.base import LLMResponse


class _FakeLLM:
    def __init__(self, response: str) -> None:
        self._response = response
        self.prompts: list[str] = []
        self.image_batches: list[list[bytes]] = []

    def invoke(self, prompt: str, images: list[bytes]) -> LLMResponse:
        self.prompts.append(prompt)
        self.image_batches.append(images)
        return LLMResponse(text=self._response)


class _RaisingLLM:
    def invoke(self, prompt, images):  # noqa: ANN001
        raise RuntimeError("model unavailable")


def _state(**overrides) -> dict:
    state = initial_state("open a web page", 10)
    state["prompt"] = "RENDERED PROMPT"
    state["screenshot_path"] = "/tmp/shot.png"
    state["retries"] = 0
    state.update(overrides)
    return state


_STUB_PNG = b"stub-png"


def _decide(response: str, loader=None):
    return make_decide(llm=_FakeLLM(response), load_screenshot=loader or _loader_bytes(_STUB_PNG))


def _loader_bytes(png: bytes):
    return lambda path: png  # noqa: ANN202


# --- decision action ---------------------------------------------------------


def test_action_decision_parses_pending_action_and_screenshot_is_sent() -> None:
    png = b"\x89PNG"
    llm = _FakeLLM('{"decision": "action", "pending_action": {"operation": "open_url", "url": "https://example.com"}}')
    node = make_decide(llm=llm, load_screenshot=_loader_bytes(png))

    update = node(_state())

    assert update["decision"] == "action"
    assert update["pending_action"] == {
        "operation": "open_url",
        "url": "https://example.com",
    }
    assert "retries" not in update
    # the screenshot bytes from the loader reached the model call
    assert llm.image_batches == [[png]]
    assert llm.prompts == ["RENDERED PROMPT"]


def test_action_decision_without_pending_action_yields_empty_dict() -> None:
    node = _decide('{"decision": "action"}')

    update = node(_state())

    assert update["decision"] == "action"
    assert update["pending_action"] == {}


# --- other decisions ---------------------------------------------------------


def test_done_decision_parses() -> None:
    update = _decide('{"decision": "done"}')(_state())

    assert update["decision"] == "done"
    assert "pending_action" not in update


def test_fail_decision_parses() -> None:
    update = _decide('{"decision": "fail"}')(_state())

    assert update["decision"] == "fail"


def test_retry_decision_bumps_retries() -> None:
    update = _decide('{"decision": "retry"}')(_state(retries=3))

    assert update["decision"] == "retry"
    assert update["retries"] == 4


# --- malformed / failed model output ----------------------------------------


def test_missing_prompt_yields_honest_fail() -> None:
    node = _decide('{"decision": "done"}')

    update = node(_state(prompt=None))

    assert update["decision"] == "fail"
    assert "hint" in update


def test_model_call_failure_yields_honest_fail() -> None:
    node = make_decide(llm=_RaisingLLM())

    update = node(_state())

    assert update["decision"] == "fail"
    assert "hint" in update


def test_non_json_response_yields_fail() -> None:
    update = _decide("certainly, here is the thing")(_state())

    assert update["decision"] == "fail"


def test_invalid_decision_value_yields_fail() -> None:
    update = _decide('{"decision": "fly_to_mars"}')(_state())

    assert update["decision"] == "fail"


def test_non_object_json_yields_fail() -> None:
    update = _decide("[1, 2, 3]")(_state())

    assert update["decision"] == "fail"


# --- screenshot loader -------------------------------------------------------


def test_screenshot_loader_is_used_when_path_present() -> None:
    png = b"\x89PNG-body"
    node = _decide('{"decision": "done"}', loader=_loader_bytes(png))

    update = node(_state(screenshot_path="/some/path.png"))

    assert update["decision"] == "done"


def test_no_screenshot_path_calls_model_without_images() -> None:
    llm = _FakeLLM('{"decision": "done"}')
    node = make_decide(llm=llm)

    node(_state(screenshot_path=None))

    assert llm.image_batches == [[]]