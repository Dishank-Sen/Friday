from __future__ import annotations

import os

import pytest

from friday.desktop.client import DesktopClient
from friday.sandbox.docker_sandbox import DockerSandbox


@pytest.mark.integration
def test_sandbox_serves_a_png() -> None:
    if os.environ.get("RUN_INTEGRATION") != "1":
        pytest.skip("set RUN_INTEGRATION=1 to run Docker integration tests")
    with DockerSandbox() as sandbox, DesktopClient(sandbox) as desktop:
        assert desktop.screenshot().startswith(b"\x89PNG\r\n\x1a\n")
        assert desktop.screen_size() == (1280, 720)
