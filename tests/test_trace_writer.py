"""The trace writer saves observation images to the trace folder."""

from __future__ import annotations

from pathlib import Path

from friday.harness.trace import ObservationTraceWriter


def test_write_image_sanitizes_name_and_returns_path(tmp_path: Path) -> None:
    writer = ObservationTraceWriter(tmp_path / "traces")

    path = writer.write_image(step_index=0, name="shot", png=b"\x89PNG\r\n\x1a\n")

    assert path == str(tmp_path / "traces" / "shot-0.png")
    assert Path(path).read_bytes() == b"\x89PNG\r\n\x1a\n"


def test_write_image_strips_directory_and_extra_suffix(tmp_path: Path) -> None:
    writer = ObservationTraceWriter(tmp_path)
    path = writer.write_image(step_index=2, name="../evil/../../name", png=b"data")

    # the name collapses to a plain basename; no directories are honored
    assert Path(path).name == "name-2.png"
    assert "evil" not in path