from pathlib import Path
from unittest.mock import Mock

import pytest

from friday.dashboard import DashboardLauncher


def test_dashboard_requires_frontend_dependencies(tmp_path: Path) -> None:
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "package.json").write_text("{}", encoding="utf-8")

    with pytest.raises(RuntimeError, match="npm install"):
        DashboardLauncher(tmp_path).start("http://viewer", "http://api")


def test_dashboard_starts_vite_with_sandbox_urls(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "package.json").write_text("{}", encoding="utf-8")
    (frontend / "node_modules").mkdir()
    process = Mock(pid=123, poll=Mock(return_value=None))
    captured: dict[str, object] = {}

    def popen(argv: list[str], **kwargs: object) -> Mock:
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return process

    monkeypatch.setattr("friday.dashboard.subprocess.Popen", popen)
    monkeypatch.setattr(DashboardLauncher, "_pick_port", staticmethod(lambda: 4173))
    monkeypatch.setattr(DashboardLauncher, "_wait_until_ready", staticmethod(lambda *_: None))

    dashboard = DashboardLauncher(tmp_path).start("http://viewer", "http://api")

    assert dashboard.url == "http://127.0.0.1:4173"
    assert captured["argv"][-5:] == ["--host", "127.0.0.1", "--port", "4173", "--strictPort"]
    environment = captured["kwargs"]["env"]
    assert isinstance(environment, dict)
    assert environment["VITE_VIEWER_URL"] == "http://viewer"
    assert environment["VITE_BACKEND_URL"] == "http://api"
