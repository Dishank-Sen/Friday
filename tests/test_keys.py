import pytest

from friday.actions.keys import normalize_key


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("ctrl+c", "ctrl+c"),
        ("control+enter", "ctrl+Return"),
        ("win+esc", "super+Escape"),
        ("F12", "F12"),
        ("pgdn", "Page_Down"),
    ],
)
def test_normalize_key(source: str, expected: str) -> None:
    assert normalize_key(source) == expected


@pytest.mark.parametrize("key", ["", "ctrl+", "ctrl+rm -rf", "F13", "semicolon"])
def test_normalize_key_rejects_invalid_token(key: str) -> None:
    with pytest.raises(ValueError):
        normalize_key(key)
