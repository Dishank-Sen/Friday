"""Tests for the shared read-only browser probe models and sanitizers."""

from __future__ import annotations

from friday.browser.models import (
    BrowserState,
    ProbeStatus,
    WaitReady,
    clean_title,
    strip_url,
)


def test_strip_url_removes_query_and_fragment() -> None:
    assert strip_url("https://x.example?a=1&b=2#frag") == "https://x.example"


def test_strip_url_keeps_scheme_host_and_path() -> None:
    assert strip_url("https://x.example/some/path?a=1") == "https://x.example/some/path"


def test_strip_url_trailing_slash_is_kept() -> None:
    assert strip_url("http://x.example/?a=1") == "http://x.example/"


def test_strip_url_empty_or_blank() -> None:
    assert strip_url("") is None
    assert strip_url(None) is None


def test_strip_url_unparsable_is_none() -> None:
    assert strip_url("not a url") is None


def test_clean_title_strips_control_chars_and_bounds_length() -> None:
    hostile = "A" * 500 + "\x00\x1f" + "\n\r\t" * 5
    cleaned = clean_title(hostile)
    assert cleaned is not None
    assert len(cleaned) <= 80
    assert "\x00" not in cleaned
    assert "\n" not in cleaned


def test_clean_title_keeps_plain_text() -> None:
    assert clean_title("GitHub") == "GitHub"


def test_clean_title_none() -> None:
    assert clean_title(None) is None


def test_browser_state_forbids_extra_fields() -> None:
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        BrowserState.model_validate({"url": "x", "not_a_field": 1})


def test_wait_ready_describes_ready_or_timeout() -> None:
    assert WaitReady(state="ready", waited_ms=5).state == "ready"
    assert WaitReady(state="timeout", waited_ms=0).state == "timeout"


def test_probe_status_carries_available_flag() -> None:
    assert ProbeStatus(available=True).available
    assert not ProbeStatus(available=False).available