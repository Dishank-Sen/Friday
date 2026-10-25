"""Tests for the pure screenshot-diff and step-outcome module."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image
from pytest import fixture

from friday.harness.verify_diff import (
    DiffResult,
    compare,
    expects_screen_change,
    step_outcome,
)
from friday.harness.verify_settings import DiffSettings


def _png_bytes(
    width: int = 100,
    height: int = 60,
    color: tuple[int, int, int] = (10, 10, 10),
) -> bytes:
    image = Image.new("RGB", (width, height), color)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _write(path: Path, data: bytes) -> Path:
    path.write_bytes(data)
    return path


@fixture
def tmpdir(tmp_path):  # noqa: ANN001
    return tmp_path


def _solid(d: Path, color: tuple, name: str) -> Path:
    return _write(d / name, _png_bytes(color=color))


# --- identical / changed ------------------------------------------------------


def test_identical_images_are_unchanged(tmpdir):
    a = _solid(tmpdir, (10, 10, 10), "a.png")
    b = _solid(tmpdir, (10, 10, 10), "b.png")

    result = compare(a, b, DiffSettings())

    assert result.label == "unchanged"
    assert result.changed_ratio == 0.0


def test_small_change_under_tolerance_is_unchanged(tmpdir):
    before = _write(tmpdir / "a.png", _png_bytes(color=(100, 100, 100)))
    after = _write(tmpdir / "b.png", _png_bytes(color=(115, 100, 100)))  # delta 15 < default 25

    result = compare(before, after, DiffSettings(tolerance=25))

    assert result.label == "unchanged"


def test_large_change_is_changed(tmpdir):
    before = _write(tmpdir / "a.png", _png_bytes(color=(10, 10, 10)))
    after = _write(tmpdir / "b.png", _png_bytes(color=(250, 250, 250)))

    result = compare(before, after, DiffSettings())

    assert result.label == "changed"
    assert result.changed_ratio is not None
    assert result.changed_ratio >= 0.9


def test_size_mismatch_is_size_changed(tmpdir):
    before = _write(tmpdir / "a.png", _png_bytes(width=100, height=60))
    after = _write(tmpdir / "b.png", _png_bytes(width=101, height=60))

    result = compare(before, after, DiffSettings())

    assert result.label == "size_changed"
    assert result.count_as_changed is True


def test_missing_file_is_unreliable(tmpdir):
    result = compare(tmpdir / "missing.png", _write(tmpdir / "b.png", _png_bytes()), DiffSettings())

    assert result.label == "unreliable"
    assert result.changed_ratio is None


def test_corrupt_file_is_unreliable(tmpdir):
    before = _write(tmpdir / "a.png", b"not a real png")
    after = _write(tmpdir / "b.png", _png_bytes())

    result = compare(before, after, DiffSettings())

    assert result.label == "unreliable"


def test_ignore_regions_exclude_self_changing_region(tmpdir):
    # a region that changes (e.g. clock) should not count as real change
    def make(base: int) -> bytes:
        image = Image.new("RGB", (100, 60), (base, base, base))
        for x in range(10, 20):
            for y in range(5, 15):
                image.putpixel((x, y), (250, 250, 250))
        out = BytesIO()
        image.save(out, format="PNG")
        return out.getvalue()

    before = _write(tmpdir / "a.png", make(50))
    after = _write(tmpdir / "b.png", make(51))  # only the region differs + tiny base change

    result = compare(before, after, DiffSettings(tolerance=25, ignore_regions=((10, 5, 10, 10),)))

    # base change of 1 is under tolerance, region ignored -> unchanged
    assert result.label == "unchanged"


# --- outcome function ---------------------------------------------------------


def test_outcome_failed_when_result_not_ok():
    assert (
        step_outcome("open_url", False, DiffResult(label="changed", changed_ratio=0.9))
        == "failed"
    )


def test_outcome_changed_when_screen_changed():
    assert (
        step_outcome("open_url", True, DiffResult(label="changed", changed_ratio=0.5))
        == "changed"
    )


def test_outcome_no_visible_change_when_expected_but_unchanged():

    assert (
        step_outcome("open_url", True, DiffResult(label="unchanged", changed_ratio=0.0))
        == "no_visible_change"
    )


def test_outcome_no_change_expected_when_expected_false():

    assert (
        step_outcome("wait", True, DiffResult(label="unchanged", changed_ratio=0.0))
        == "no_change_expected"
    )


def test_outcome_unknown_when_diff_unreliable():
    assert (
        step_outcome("open_url", True, DiffResult(label="unreliable", changed_ratio=None))
        == "unknown"
    )


# --- EXPECTS_SCREEN_CHANGE table ----------------------------------------------


def test_expected_change_operations():
    ops = (
        "left_click",
        "type",
        "key",
        "shortcut",
        "open_url",
        "launch_app",
        "scroll",
        "focus_window",
    )
    for op in ops:
        assert expects_screen_change(op), op


def test_no_expected_change_operations():
    ops = (
        "wait",
        "mouse_move",
        "hold_key",
        "screenshot",
        "read_file",
        "get_clipboard",
        "list_windows",
    )
    for op in ops:
        assert not expects_screen_change(op), op