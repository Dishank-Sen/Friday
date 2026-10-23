"""FastAPI service that controls the container's X11 desktop."""

from __future__ import annotations

import hmac
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Response, status
from pydantic import BaseModel, Field

AUTH_TOKEN_ENV = "FRIDAY_CONTROL_TOKEN"
DISPLAY_ENV = "DISPLAY"
DEFAULT_DISPLAY = ":1"

app = FastAPI(title="Friday desktop control", docs_url=None, redoc_url=None)


class ClickRequest(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    button: int = Field(default=1, ge=1, le=5)


class TypeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)


class KeyRequest(BaseModel):
    combo: str = Field(min_length=1, max_length=256)


def _token() -> str:
    token = os.environ.get(AUTH_TOKEN_ENV)
    if not token:
        raise RuntimeError(f"{AUTH_TOKEN_ENV} must be set")
    return token


def require_auth(authorization: Annotated[str | None, Header()] = None) -> None:
    expected = _token()
    scheme, _, supplied = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not hmac.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(args),
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, DISPLAY_ENV: os.environ.get(DISPLAY_ENV, DEFAULT_DISPLAY)},
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "command failed"
        raise HTTPException(status_code=502, detail=detail)
    return result


def _screen_size() -> tuple[int, int]:
    output = _run("xdotool", "getdisplaygeometry").stdout.strip().split()
    if len(output) != 2:
        raise HTTPException(status_code=502, detail="xdotool returned invalid display geometry")
    try:
        width, height = (int(value) for value in output)
    except ValueError as error:
        raise HTTPException(status_code=502, detail="xdotool returned invalid display geometry") from error
    return width, height


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/screenshot", dependencies=[Depends(require_auth)])
def screenshot() -> Response:
    descriptor, image_name = tempfile.mkstemp(suffix=".png")
    os.close(descriptor)
    image = Path(image_name)
    image.unlink()
    try:
        _run("scrot", "--", str(image))
        content = image.read_bytes()
    except FileNotFoundError as error:
        raise HTTPException(status_code=502, detail="scrot did not create a screenshot") from error
    finally:
        image.unlink(missing_ok=True)
    if not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(status_code=502, detail="scrot did not produce a PNG image")
    return Response(content=content, media_type="image/png")


@app.get("/screen_size", dependencies=[Depends(require_auth)])
def screen_size() -> dict[str, int]:
    width, height = _screen_size()
    return {"width": width, "height": height}


@app.post("/click", dependencies=[Depends(require_auth)])
def click(request: ClickRequest) -> dict[str, bool]:
    width, height = _screen_size()
    if request.x >= width or request.y >= height:
        raise HTTPException(status_code=422, detail="coordinates are outside the display")
    _run("xdotool", "mousemove", str(request.x), str(request.y), "click", str(request.button))
    return {"ok": True}


@app.post("/type", dependencies=[Depends(require_auth)])
def type_text(request: TypeRequest) -> dict[str, bool]:
    _run("xdotool", "type", "--delay", "0", "--", request.text)
    return {"ok": True}


@app.post("/key", dependencies=[Depends(require_auth)])
def key(request: KeyRequest) -> dict[str, bool]:
    _run("xdotool", "key", "--", request.combo)
    return {"ok": True}
