import pytest

from friday.actions.focus import focused_app_for


@pytest.mark.parametrize(
    ("class_name", "expected"),
    [
        ("chromium (/tmp/profile).Chromium", "browser"),
        ("XFCE4-TERMINAL.Xfce4-terminal", "terminal"),
        ("thunar-real.Thunar-real", "file_manager"),
        ("org.xfce.mousepad.Org.xfce.mousepad", "text_editor"),
        ("chromium-custom.Unknown", "browser"),
        ("unknown.Chromium", "browser"),
        ("", "other"),
        (None, "other"),
        ("other.Other", "other"),
    ],
)
def test_focused_app_for(class_name: str | None, expected: str) -> None:
    assert focused_app_for(class_name) == expected
