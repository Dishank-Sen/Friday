"""Lifecycle management for the standalone Friday dashboard."""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Dashboard:
    url: str
    pid: int


class DashboardLauncher:
    def __init__(self, project_root: Path) -> None:
        self._frontend = project_root / "frontend"

    def start(self, viewer_url: str, backend_url: str) -> Dashboard:
        if not (self._frontend / "package.json").is_file():
            raise RuntimeError("frontend/package.json is missing")
        if not (self._frontend / "node_modules").is_dir():
            raise RuntimeError("frontend dependencies are missing; run `npm install` in frontend/")
        port = self._pick_port()
        process = subprocess.Popen(
            ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", str(port), "--strictPort"],
            cwd=self._frontend,
            env={**os.environ, "VITE_VIEWER_URL": viewer_url, "VITE_BACKEND_URL": backend_url},
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        url = f"http://127.0.0.1:{port}"
        self._wait_until_ready(process, port)
        return Dashboard(url=url, pid=process.pid)

    @staticmethod
    def stop(pid: int | None) -> None:
        if pid is None:
            return
        try:
            os.killpg(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            return

    @staticmethod
    def _pick_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", 0))
            return int(probe.getsockname()[1])

    @staticmethod
    def _wait_until_ready(process: subprocess.Popen[bytes], port: int) -> None:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Friday dashboard exited while starting")
            try:
                with socket.create_connection(("127.0.0.1", port), 0.2):
                    return
            except OSError:
                time.sleep(0.1)
        DashboardLauncher.stop(process.pid)
        raise RuntimeError("Friday dashboard did not become ready within 15 seconds")
