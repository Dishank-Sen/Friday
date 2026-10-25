"""FastAPI service that controls the container's X11 desktop."""

from __future__ import annotations

import hmac
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Response, status
from pydantic import ValidationError

from friday.actions.models import ActionResult, parse_action
from friday.browser.models import BrowserState, ProbeStatus, WaitReady
from friday.desktop.observation import ActiveWindow, Observation
from friday.operations.registry import OperationError, parse_operation
from server.backend.base import BackendError, DesktopBackend
from server.backend.browser import BrowserBackend
from server.backend.runner import SubprocessRunner
from server.backend.x11 import X11Backend

AUTH_TOKEN_ENV = "FRIDAY_CONTROL_TOKEN"
DISPLAY_ENV = "DISPLAY"
DEFAULT_DISPLAY = ":1"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    workspace = Path(os.environ.get("FRIDAY_WORKSPACE", "/config/friday-workspace"))
    workspace.mkdir(parents=True, exist_ok=True)
    backend = X11Backend(SubprocessRunner(os.environ.get(DISPLAY_ENV, DEFAULT_DISPLAY)), workspace)
    app.state.backend = backend
    app.state.browser_backend = BrowserBackend()
    try:
        yield
    finally:
        backend.release_all()


app = FastAPI(title="Friday desktop control", docs_url=None, redoc_url=None, lifespan=lifespan)


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


def _backend() -> DesktopBackend:
    return app.state.backend


def _backend_error(error: BackendError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/screenshot", dependencies=[Depends(require_auth)])
def screenshot() -> Response:
    try:
        content = _backend().screenshot()
    except BackendError as error:
        raise _backend_error(error) from error
    return Response(content=content, media_type="image/png")


@app.get("/screen_size", dependencies=[Depends(require_auth)])
def screen_size() -> dict[str, int]:
    try:
        width, height = _backend().screen_size()
    except BackendError as error:
        raise _backend_error(error) from error
    return {"width": width, "height": height}


@app.get("/cursor", dependencies=[Depends(require_auth)])
def cursor() -> dict[str, int]:
    try:
        x, y = _backend().cursor_position()
    except BackendError as error:
        raise _backend_error(error) from error
    return {"x": x, "y": y}


@app.get("/observation", dependencies=[Depends(require_auth)], response_model=Observation)
def observation() -> Observation:
    try:
        return _backend().observation()
    except BackendError as error:
        raise _backend_error(error) from error


@app.get("/active_window", dependencies=[Depends(require_auth)], response_model=ActiveWindow)
def active_window() -> ActiveWindow:
    try:
        return _backend().active_window()
    except BackendError as error:
        raise _backend_error(error) from error


@app.post("/action", dependencies=[Depends(require_auth)], response_model=ActionResult)
def action(payload: dict[str, object]) -> ActionResult:
    try:
        desktop_action = parse_action(payload)
    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=error.errors()
        ) from error
    try:
        return _backend().execute(desktop_action)
    except BackendError as error:
        raise _backend_error(error) from error


@app.post("/operation", dependencies=[Depends(require_auth)])
def operation(payload: dict[str, object]) -> dict[str, object]:
    try:
        system_operation = parse_operation(payload, _backend().workspace)
    except (OperationError, ValidationError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    try:
        return _backend().execute_operation(system_operation)
    except BackendError as error:
        raise _backend_error(error) from error


def _browser() -> BrowserBackend:
    return app.state.browser_backend


@app.get("/browser/available", dependencies=[Depends(require_auth)])
def browser_available() -> ProbeStatus:
    return _browser().available()


@app.get("/browser/state", dependencies=[Depends(require_auth)])
def browser_state() -> BrowserState:
    return _browser().state()


@app.post("/browser/wait_ready", dependencies=[Depends(require_auth)])
def browser_wait_ready(payload: dict[str, object]) -> WaitReady:
    timeout_s = payload.get("timeout_s", 5.0)
    if not isinstance(timeout_s, (int, float)) or timeout_s <= 0 or timeout_s > 30:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="timeout_s must be a positive number <= 30",
        )
    return _browser().wait_ready(float(timeout_s))
