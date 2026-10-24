from pathlib import Path

import pytest

from friday.desktop.observation import (
    capture_observation,
    decimal_window_id_to_hex,
    parse_active_window,
    parse_windows,
    sanitize_title,
)

FIXTURES = Path(__file__).parent / "fixtures" / "observation"


def test_capture_observation_parses_real_container_fixture() -> None:
    observation = capture_observation(
        b"\x89PNG\r\n\x1a\n",
        "1280 720\n",
        (FIXTURES / "wmctrl_lpgx.txt").read_text(encoding="utf-8"),
        (FIXTURES / "active_window.txt").read_text(encoding="utf-8"),
    )

    assert observation.active_window_id == "0x03000002"
    assert observation.active_window_class == "chromium (/tmp/friday-chromium-debug).Chromium"
    assert observation.focused_app == "browser"
    assert [window.id for window in observation.windows] == [
        "0x03000002", "0x01600003", "0x02e00007", "0x02c00003"
    ]
    assert set(observation.windows[0].model_dump()) == {"id", "title", "class_name", "active"}


def test_window_parser_sanitizes_caps_and_ignores_background() -> None:
    lines = [
        "0x00000001 -1 1 0 0 1 1 xfce4-panel.Xfce4-panel  host panel",
        "0x00000002 -1 2 0 0 1 1 xfdesktop.Xfdesktop  host desktop",
    ]
    lines.extend(
        f"0x{index:08x} 0 {index} 0 0 1 1 App.Class  host title {index}"
        for index in range(3, 21)
    )
    lines.append("malformed")

    windows = parse_windows("\n".join(lines), "0x00000014")

    assert len(windows) == 15
    assert windows[0].id == "0x00000014"
    assert all("geometry" not in window.model_dump() for window in windows)


@pytest.mark.parametrize(
    ("source", "expected"),
    [("  hello\x00\n  world\t" * 20, "hello world " * 7 + "hello "), ("", "")],
)
def test_title_sanitization(source: str, expected: str) -> None:
    assert sanitize_title(source) == expected[:80]


@pytest.mark.parametrize(
    ("source", "expected"), [("50331650\n", "0x03000002"), ("", None), ("bad", None)]
)
def test_decimal_window_id_conversion(source: str, expected: str | None) -> None:
    assert decimal_window_id_to_hex(source) == expected


def test_malformed_observation_output_is_safe() -> None:
    with pytest.raises(ValueError, match="geometry"):
        capture_observation(b"png", "bad", "malformed", "bad")
    active = parse_active_window("malformed", "bad")
    assert active.id is None
    assert active.focused_app == "other"
