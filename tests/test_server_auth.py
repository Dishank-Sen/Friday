from __future__ import annotations

import pytest
from fastapi import HTTPException

from server import app


def test_auth_accepts_matching_bearer_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(app.AUTH_TOKEN_ENV, "expected")

    app.require_auth("Bearer expected")


@pytest.mark.parametrize("authorization", [None, "Basic expected", "Bearer wrong"])
def test_auth_rejects_missing_or_wrong_token(
    monkeypatch: pytest.MonkeyPatch, authorization: str | None
) -> None:
    monkeypatch.setenv(app.AUTH_TOKEN_ENV, "expected")

    with pytest.raises(HTTPException) as error:
        app.require_auth(authorization)

    assert error.value.status_code == 401
