from __future__ import annotations

import os
from pathlib import Path

import pytest

from friday.actions.models import CursorPositionAction, MouseMoveAction
from friday.desktop.client import DesktopClient
from friday.executor.remote import RemoteExecutor
from friday.operations.registry import parse_operation
from friday.sandbox.docker_sandbox import DockerSandbox


@pytest.mark.integration
def test_sandbox_serves_a_png() -> None:
    if os.environ.get("RUN_INTEGRATION") != "1":
        pytest.skip("set RUN_INTEGRATION=1 to run Docker integration tests")
    with DockerSandbox() as sandbox, DesktopClient(sandbox) as desktop:
        assert desktop.screenshot().startswith(b"\x89PNG\r\n\x1a\n")
        assert desktop.screen_size() == (1280, 720)
        executor = RemoteExecutor(desktop)
        assert executor.execute(MouseMoveAction(action="mouse_move", x=10, y=10)).ok
        assert executor.execute(CursorPositionAction(action="cursor_position")).point == (10, 10)
        operation = parse_operation({"operation": "list_windows"}, Path("/config/friday-workspace"))
        assert "output" in desktop.operation(operation)
