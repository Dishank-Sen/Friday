"""Execution of validated system operations."""

from __future__ import annotations

import os
import shutil
import signal
import time
from pathlib import Path

from friday.operations.registry import (
    CloseApp,
    DeleteFile,
    GetClipboard,
    ListDir,
    ReadFile,
    SetClipboard,
    SystemOperation,
    WriteFile,
    _path,
)

from .base import BackendError
from .commands import command_for_operation
from .runner import CommandRunner


class SystemBackend:
    def __init__(self, runner: CommandRunner, workspace: Path) -> None:
        self._runner = runner
        self._workspace = workspace.resolve()
        self._started_pids: set[int] = set()

    @property
    def workspace(self) -> Path:
        return self._workspace

    def execute(self, operation: SystemOperation) -> dict[str, object]:
        started = time.monotonic()
        try:
            result = self._execute(operation)
        except OSError as error:
            raise BackendError(str(error)) from error
        result["duration_seconds"] = round(time.monotonic() - started, 3)
        return result

    def _execute(self, operation: SystemOperation) -> dict[str, object]:
        def path(value: str) -> Path:
            return Path(_path(value, self._workspace))
        if isinstance(operation, ReadFile):
            return {"content": path(operation.path).read_text(encoding="utf-8")}
        if isinstance(operation, WriteFile):
            path(operation.path).write_text(operation.content, encoding="utf-8")
            return {"ok": True}
        if isinstance(operation, ListDir):
            return {"entries": sorted(item.name for item in path(operation.path).iterdir())}
        if operation.operation == "make_dir":
            path(operation.path).mkdir(parents=True, exist_ok=True)
            return {"ok": True}
        if isinstance(operation, DeleteFile):
            target = path(operation.path)
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            return {"ok": True}
        if isinstance(operation, CloseApp):
            if operation.pid not in self._started_pids:
                raise BackendError("pid was not started by Friday")
            os.kill(operation.pid, signal.SIGTERM)
            self._started_pids.discard(operation.pid)
            return {"ok": True}
        argv = command_for_operation(operation, self._workspace)
        if argv is None:
            raise BackendError(f"unsupported operation: {operation.operation}")
        if operation.operation.startswith(("launch_", "open_")):
            process = self._runner.start(argv)
            self._started_pids.add(process.pid)
            return {"pid": process.pid}
        stdin = operation.text if isinstance(operation, SetClipboard) else None
        output = self._runner.run(argv, stdin=stdin, timeout=getattr(operation, "timeout", 10.0))
        if isinstance(operation, GetClipboard):
            return {"text": output}
        return {"output": output, "ok": True}
