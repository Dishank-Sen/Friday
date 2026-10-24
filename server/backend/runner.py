from __future__ import annotations

import os
import subprocess
from typing import Protocol

from .base import BackendError


class CommandRunner(Protocol):
    def run(self, argv: list[str], *, stdin: str | None = None, timeout: float = 10.0) -> str: ...

    def start(self, argv: list[str]) -> subprocess.Popen[bytes]: ...


class SubprocessRunner:
    def __init__(self, display: str) -> None:
        self._display = display

    def run(self, argv: list[str], *, stdin: str | None = None, timeout: float = 10.0) -> str:
        result = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            input=stdin,
            timeout=timeout,
            env={**os.environ, "DISPLAY": self._display},
        )
        if result.returncode:
            detail = result.stderr.strip() or result.stdout.strip() or "command failed"
            raise BackendError(detail)
        return result.stdout

    def start(self, argv: list[str]) -> subprocess.Popen[bytes]:
        return subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            env={**os.environ, "DISPLAY": self._display},
        )
