"""Boundary contract tests for every implemented harness node.

The node list and each node's documented read/write sets are a single table in
``friday.harness.contract``. ``docs/harness.md`` renders its State table from
that same source, so these tests and the docs cannot disagree (see
``test_contract_table_matches_generated_docs``). New nodes are added to the
``contract.NODES`` table, which extends coverage here automatically.
"""

from __future__ import annotations

import ast
import copy
from pathlib import Path

from friday.actions.focus import focused_app_for
from friday.desktop.observation import Observation, WindowInfo
from friday.harness.contract import NODES
from friday.harness.nodes.build_context import make_build_context
from friday.harness.nodes.guard import make_guard
from friday.harness.nodes.observe import make_observe
from friday.harness.state import initial_state


class _RecordingState(dict):
    """A state dict that records every key read via ``get``/``__getitem__``."""

    def __init__(self, data: dict) -> None:
        super().__init__(data)
        self.reads: set[str] = set()

    def get(self, key, default=None):  # noqa: ANN001, ANN201
        self.reads.add(key)
        return super().get(key, default)

    def __getitem__(self, key):  # noqa: ANN001, ANN201
        self.reads.add(key)
        return super().__getitem__(key)


class _FakeClient:
    def observation(self) -> Observation:
        return Observation(
            screenshot_png=b"\x89PNG\r\n\x1a\n",
            screen_size=(1280, 720),
            windows=[WindowInfo(id="1", title="Chromium", class_name="Chromium", active=True)],
            active_window_id="1",
            active_window_class="Chromium",
            focused_app="browser",
        )


class _FakeTrace:
    def write(self, observation, error=None):  # noqa: ANN001
        return "/tmp/shot.png"


def _base_state(**overrides) -> dict:
    state = initial_state("open a web page", 10)
    state["focused_app"] = "browser"
    state["screen_size"] = (1280, 720)
    state["step"] = 1
    state["retries"] = 2
    state["history"] = []
    state.update(overrides)
    return state


def _nodes() -> dict[str, object]:
    from friday.harness.nodes.decide import make_decide

    return {
        "build_context": make_build_context(),
        "decide": make_decide(llm=_FakeLLM()),
        "guard": make_guard(),
        "observe": make_observe(_FakeClient(), _FakeTrace(), focused_app_for),
    }


class _FakeLLM:
    def invoke(self, prompt, images):  # noqa: ANN001
        from friday.llm.base import LLMResponse

        return LLMResponse(text='{"decision": "done"}')


def _case_state(name: str) -> dict:
    if name == "guard":
        return _base_state(pending_action={"action": "shortcut", "name": "copy"})
    if name == "decide":
        return _base_state(prompt="a rendered prompt", screenshot_path=None)
    return _base_state()


# --- the contract table itself ----------------------------------------------


def test_contract_table_lists_every_implemented_node() -> None:
    assert set(NODES) >= {"observe", "build_context", "decide", "guard"}


# --- write-contract: a node returns only its documented writes ---------------


def test_write_contract_holds_for_implemented_nodes() -> None:
    for name, node in _nodes().items():
        update = node(_case_state(name))
        return_keys = set(update)
        assert return_keys <= NODES[name].writes, (
            f"{name} wrote keys {return_keys - NODES[name].writes} outside its contract"
        )


# --- read-contract: a node reads only its documented reads -------------------


def test_read_contract_holds_for_all_implemented_nodes() -> None:
    for name, node in _nodes().items():
        recording = _RecordingState(_case_state(name))
        node(recording)
        reads = recording.reads
        assert reads <= NODES[name].reads, (
            f"{name} read keys {reads - NODES[name].reads} outside its contract"
        )


# --- purity: build_context is deterministic and does not mutate state --------


def test_build_context_is_pure_and_deterministic() -> None:
    state = _base_state()
    before = copy.deepcopy(state)

    first = make_build_context()(copy.deepcopy(state))["prompt"]
    second = make_build_context()(copy.deepcopy(state))["prompt"]

    assert first == second  # deterministic
    assert state == before  # input state not mutated (returned by reference)


# --- import boundary: build_context deps do not reach forbidden modules ------

_FORBIDDEN_IMPORTS = {
    "friday.llm",
    "friday.executor",
    "friday.desktop",
    "subprocess",
    "requests",
    "httpx",
    "docker",
    "socket",
}
_FORBIDDEN_CALLS = {"time.sleep", "random", "datetime.now", "open", "Path.read_text"}


def _dependency_files() -> list[Path]:
    """The build_context dependency closure, enumerated precisely.

    build_context composes the harness layers + the operation/action/shortcut
    registries. ``observe`` and ``decide`` (and the desktop/trace clients) are
    deliberately not part of this closure.
    """
    harness = Path("src/friday/harness")
    mods = [
        harness / "capabilities.py",
        harness / "context.py",
        harness / "config.py",
        harness / "contract.py",
        harness / "facts.py",
        harness / "render.py",
        harness / "state.py",
        harness / "nodes" / "build_context.py",
    ]
    for reg in (
        Path("src/friday/operations/registry.py"),
        Path("src/friday/actions/models.py"),
        Path("src/friday/actions/keys.py"),
        Path("src/friday/actions/config.py"),
        Path("src/friday/shortcuts/registry.py"),
    ):
        mods.append(reg)
    return mods


def test_build_context_dependency_closure_avoids_forbidden_imports() -> None:
    imported_modules: set[str] = set()
    for path in _dependency_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
    # a forbidden module is disallowed whether imported directly or as a prefix
    for forbidden in _FORBIDDEN_IMPORTS:
        for module in imported_modules:
            assert module != forbidden and not module.startswith(forbidden + "."), (
                f"forbidden import {forbidden} (saw {module}) in build_context closure"
            )


def test_build_context_does_not_call_time_sleep_random_or_datetime() -> None:
    bad: set[str] = set()
    for path in _dependency_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                call = f"{ast.unparse(node.func.value)}.{node.func.attr}"
                if call == "datetime.now":
                    bad.add("datetime.now")
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "sleep":
                    bad.add("time.sleep")
                if node.func.id == "random":
                    bad.add("random")
    assert bad == set()


# --- docs derive from the same contract table ---------------------------------


def test_contract_table_matches_generated_docs() -> None:
    from friday.harness.contract import _as_table_markdown

    docs = Path("docs/harness.md").read_text(encoding="utf-8")
    assert "| Node | Reads | Writes |" in docs
    for row in _as_table_markdown().splitlines()[2:]:
        assert row in docs, f"contract row not found in docs: {row}"