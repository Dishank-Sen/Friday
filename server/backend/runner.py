from __future__ import annotations

import os
import subprocess
from typing import Protocol

from .base import BackendError


class CommandRunner(Protocol):
    def run(self, argv: list[str]) -> str: ...


class SubprocessRunner:
    def __init__(self, display: str) -> None:
        self._display = display

    def run(self, argv: list[str]) -> str:
        result = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, "DISPLAY": self._display},
        )
        if result.returncode:
            detail = result.stderr.strip() or result.stdout.strip() or "command failed"
            raise BackendError(detail)
        return result.stdout
