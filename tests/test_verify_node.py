"""Tests for the real verify node: diff-based outcome, bookkeeping, history."""

from __future__ import annotations

from io import BytesIO

from PIL import Image

from friday.harness.nodes.verify import VerifyDeps, make_verify
from friday.harness.state import initial_state
from friday.harness.verify_settings import DiffSettings, VerifySettings


def _png_bytes(width: int = 100, height: int = 60, color=(10, 10, 10)) -> bytes:
    image = Image.new("RGB", (width, height), color)
    out = BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


class _Probe:
    def __init__(self, state=None, fail=False) -> None:
        self._state = state or {"tab_count": 1, "url": "https://github.com/Dishank-Sen?a=1"}
        self.fail = fail
        self.calls = 0

    def state(self):
        self.calls += 1
        if self.fail:
            raise RuntimeError("probe down")
        return dict(self._state)

    def wait_ready(self, timeout_s: float) -> dict:
        return {"state": "ready", "waited_ms": 0}


def _loader(*, prev=None, cur=None, missing: str | None = None):
    def load(path: str) -> bytes:
        if missing and path == missing:
            raise FileNotFoundError(path)
        return bytes(path.encode()) if path else b""

    return load


class _Files:
    def __init__(self, tmp_path) -> None:  # noqa: ANN001
        self.prev = tmp_path / "prev.png"
        self.cur = tmp_path / "cur.png"


def _base(tmp_path, **overrides) -> dict:
    files = _Files(tmp_path)
    files.prev.write_bytes(_png_bytes(color=(10, 10, 10)))
    files.cur.write_bytes(_png_bytes(color=(250, 250, 250)))
    state = initial_state("open a page", 10)
    state["decision"] = "action"
    state["pending_action"] = {"action": "open_url", "url": "https://x.example"}
    state["last_result"] = {"ok": True, "operation": "open_url"}
    state["step"] = 2
    state["stuck_count"] = 0
    state["history"] = []
    state["screenshot_path"] = str(files.cur)
    state["prev_screenshot_path"] = str(files.prev)
    state.update(overrides)
    return state


def _node(loader=None, probe=None, settings=None, **kw) -> object:  # noqa: ANN001
    deps = VerifyDeps(
        load_screenshot=loader or _loader(),
        settings=settings or VerifySettings(),
        probe=probe,
    )
    return make_verify(deps=deps, **kw)


# --- diff-driven outcome -----------------------------------------------------


def test_changed_screen_records_changed_outcome_and_resets_stuck(tmp_path) -> None:
    node = _node(loader=_loader(), probe=_Probe())
    state = _base(
        tmp_path,
        step=3,
        stuck_count=2,
    )

    result = node(state)

    assert result["step"] == 4
    assert result["stuck_count"] == 0
    assert result["history"][-1]["outcome"] == "changed"
    assert result["history"][-1]["changed_ratio"] is not None


def test_unchanged_screen_when_change_expected_is_no_visible_change(tmp_path) -> None:
    state = _base(tmp_path)
    files = _Files(tmp_path)
    # overwrite the difference-case files with identical images AFTER _base
    files.prev.write_bytes(_png_bytes(color=(40, 40, 40)))
    files.cur.write_bytes(_png_bytes(color=(40, 40, 40)))
    state["prev_screenshot_path"] = str(files.prev)
    state["screenshot_path"] = str(files.cur)

    node = _node(loader=_loader(), probe=_Probe())

    result = node(state)

    assert result["history"][-1]["outcome"] == "no_visible_change"
    assert result["stuck_count"] == 1
    assert result["hint"]  # stalled-step hint written


def test_no_change_expected_for_wait_is_not_stuck(tmp_path) -> None:
    state = _base(
        tmp_path,
        pending_action={"action": "wait", "seconds": 1},
        last_result={"ok": True, "operation": "wait"},
    )
    files = _Files(tmp_path)
    files.prev.write_bytes(_png_bytes(color=(40, 40, 40)))
    files.cur.write_bytes(_png_bytes(color=(40, 40, 40)))
    state["prev_screenshot_path"] = str(files.prev)
    state["screenshot_path"] = str(files.cur)

    node = _node(loader=_loader(), probe=_Probe())

    result = node(state)

    assert result["history"][-1]["outcome"] == "no_change_expected"
    # no_change_expected leaves stuck_count unchanged (0 -> no key or 0)
    assert result.get("stuck_count", 0) == 0


def test_failed_result_is_failed_and_increments_stuck(tmp_path) -> None:
    node = _node(loader=_loader(), probe=_Probe())
    state = _base(tmp_path, last_result={"ok": False, "operation": "left_click"}, stuck_count=1)

    result = node(state)

    assert result["history"][-1]["outcome"] == "failed"
    assert result["stuck_count"] == 2


def test_unusable_screenshots_are_unknown(tmp_path) -> None:
    node = _node(loader=_loader(missing="missing"), probe=_Probe())
    state = _base(tmp_path)
    state["prev_screenshot_path"] = "missing"
    state["screenshot_path"] = str(_Files(tmp_path).prev)

    result = node(state)

    assert result["history"][-1]["outcome"] == "unknown"
    assert result.get("stuck_count", 0) == 0


# --- step bookkeeping / bounds ------------------------------------------------


def test_step_increments_per_executed_action(tmp_path) -> None:
    node = _node(loader=_loader())
    state = _base(tmp_path, step=5)

    result = node(state)

    assert result["step"] == 6


def test_history_is_bounded(tmp_path) -> None:
    settings = VerifySettings(diff=DiffSettings(max_history=3))
    node = _node(loader=_loader(), settings=settings, probe=_Probe())
    prior = [{"decision": "action", "outcome": "changed", "action": {"action": "wait"}}] * 5
    state = _base(tmp_path, history=list(prior))

    result = node(state)

    assert len(result["history"]) <= 3


def test_existing_hint_is_not_overwritten(tmp_path) -> None:
    state = _base(tmp_path)
    state["hint"] = "keep me"
    # use an operation that does not produce a new hint (existing hint stays)
    state["pending_action"] = {"action": "wait", "seconds": 1}
    state["last_result"] = {"ok": True, "operation": "wait"}

    node = _node(loader=_loader(), probe=_Probe())
    result = node(state)

    # verify must NOT emit a hint when it has none new, so the existing one
    # survives (state merge preserves it)
    assert "hint" not in result


# --- history record shape matches guard + facts consumers ----------------------


def test_history_record_shape_is_compatible_with_consumers(tmp_path) -> None:
    from friday.harness.facts import _history_entry

    node = _node(loader=_loader(), probe=_Probe())
    pending = {"action": "open_url", "url": "https://x.example", "expected_result": "github loads"}
    state = _base(tmp_path, decision="action", pending_action=pending)

    result = node(state)
    entry = result["history"][-1]

    # facts consumer reads decision/outcome/action and does not crash
    norm = _history_entry(entry, 400)
    assert "decision" in norm
    assert "outcome" in norm
    # guard repeat check reads action (operation discriminator)
    assert entry["action"] == pending
    # our added fields are present
    assert entry["operation"] == "open_url"
    assert entry["expected_result"] == "github loads"
    # expected_result is copied unchanged from pending_action


def test_typed_text_canary_never_in_history(tmp_path) -> None:
    node = _node(loader=_loader(), probe=_Probe())
    state = _base(
        tmp_path,
        pending_action={"action": "type", "text": "the-secret-typed-token"},
        last_result={"ok": True, "operation": "type"},
    )

    result = node(state)
    dumped = str(result["history"])

    assert "the-secret-typed-token" not in dumped
    # type summarized by length
    entry = result["history"][-1]
    assert entry["ok"] is True


def test_url_is_stripped_of_query_in_browser_facts(tmp_path) -> None:
    probe = _Probe({"url": "https://x.example?a=1&b=2", "title": "Github"})
    node = _node(loader=_loader(), probe=probe)
    state = _base(tmp_path)

    result = node(state)
    entry = result["history"][-1]

    assert "browser" in entry
    assert "?" not in entry["browser"]["url"]
    assert "#" not in entry["browser"]["url"]


def test_hostile_title_is_bounded_and_sanitized(tmp_path) -> None:
    hostile = "A" * 500 + "\x00\x1f" + "\n" * 3
    node = _node(loader=_loader(), probe=_Probe({"url": "https://x.example", "title": hostile}))
    state = _base(tmp_path)

    result = node(state)
    entry = result["history"][-1]

    title = entry["browser"]["title"]
    assert len(title) <= 80
    assert "\x00" not in title and "\n" not in title


def test_no_browser_facts_when_probe_absent(tmp_path) -> None:
    node = _node(loader=_loader(), probe=None)
    state = _base(tmp_path)

    result = node(state)

    assert "browser" not in result["history"][-1]


def test_no_browser_facts_when_probe_failing(tmp_path) -> None:
    node = _node(loader=_loader(), probe=_Probe(fail=True))
    state = _base(tmp_path)

    result = node(state)

    assert "browser" not in result["history"][-1]


# --- contract: write-only step/history/stuck_count/hint ------------------------


def test_verify_writes_only_contract_fields(tmp_path) -> None:
    node = _node(loader=_loader(), probe=_Probe())
    state = _base(tmp_path)

    result = node(state)

    assert set(result.keys()) <= {"step", "history", "stuck_count", "hint"}


def test_verify_reads_only_contract_fields(tmp_path) -> None:
    class R(dict):
        def __init__(self, d: dict) -> None:
            super().__init__(d)
            self.reads: set[str] = set()

        def get(self, key, default=None):
            self.reads.add(key)
            return super().get(key, default)

    node = _node(loader=_loader(), probe=_Probe())
    state = _base(tmp_path)
    recording = R(state)

    node(recording)

    allowed = {
        "decision",
        "pending_action",
        "last_result",
        "history",
        "step",
        "stuck_count",
        "screenshot_path",
        "prev_screenshot_path",
        "hint",
    }
    assert recording.reads <= allowed, recording.reads - allowed


def test_verify_does_not_mutate_input_state(tmp_path) -> None:
    import copy

    node = _node(loader=_loader(), probe=_Probe())
    state = _base(tmp_path)
    before = copy.deepcopy(state)

    node(state)

    assert state == before