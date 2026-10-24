"""Command-line entry point for Friday."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from pydantic import ValidationError

from friday.actions.models import parse_action
from friday.config import FridayConfig
from friday.dashboard import Dashboard, DashboardLauncher
from friday.desktop.client import DesktopClient
from friday.desktop.errors import DesktopError
from friday.executor.remote import RemoteExecutor
from friday.graph.locate import LocateRunner
from friday.llm import LLMError, create_llm
from friday.llm.config import LLMSettings
from friday.operations.registry import parse_operation
from friday.sandbox.docker_sandbox import DockerSandbox
from friday.vision.annotate import annotate_crosshair

STATE_FILE = Path(".friday-state.json")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a local Friday desktop sandbox")
    parser.add_argument("--docker-image", default=FridayConfig().image)
    parser.add_argument("--name", default=FridayConfig().container_name)
    parser.add_argument("--viewer-port", type=int)
    parser.add_argument("--api-port", type=int)
    parser.add_argument("--width", type=int, default=FridayConfig().width)
    parser.add_argument("--height", type=int, default=FridayConfig().height)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("up")
    subparsers.add_parser("down")
    subparsers.add_parser("status")
    screenshot = subparsers.add_parser("screenshot")
    screenshot.add_argument("output", type=Path)
    act = subparsers.add_parser("act")
    act.add_argument("payload", help="JSON action object")
    act.add_argument("--screenshot", type=Path, metavar="OUTPUT")
    operation = subparsers.add_parser("operation")
    operation.add_argument("payload", help="JSON system operation object")
    locate = subparsers.add_parser("locate")
    locate.add_argument("instruction")
    source = locate.add_mutually_exclusive_group(required=True)
    source.add_argument("--image", type=Path)
    source.add_argument("--live", action="store_true")
    locate.add_argument("--annotate", type=Path)
    return parser


def _config(args: argparse.Namespace) -> FridayConfig:
    return FridayConfig(
        image=args.docker_image,
        container_name=args.name,
        viewer_port=args.viewer_port,
        api_port=args.api_port,
        width=args.width,
        height=args.height,
    )


def _write_state(sandbox: DockerSandbox, dashboard: Dashboard) -> None:
    state = {
        "config": asdict(sandbox.config),
        "viewer_port": sandbox.viewer_url.rsplit(":", maxsplit=1)[1],
        "api_port": sandbox.api_url.rsplit(":", maxsplit=1)[1],
        "token": sandbox.token,
        "dashboard_url": dashboard.url,
        "dashboard_pid": dashboard.pid,
    }
    STATE_FILE.write_text(json.dumps(state), encoding="utf-8")


def _load_sandbox() -> DockerSandbox:
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        config_data = dict(state["config"])
        config_data["token"] = state["token"]
        return DockerSandbox.from_existing(
            FridayConfig(**config_data),
            viewer_port=int(state["viewer_port"]),
            api_port=int(state["api_port"]),
            token=state["token"],
        )
    except (FileNotFoundError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise RuntimeError("Friday is not running; use `python -m friday up` first") from error


def _dashboard_state() -> tuple[str | None, int | None]:
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        url = state.get("dashboard_url")
        pid = state.get("dashboard_pid")
        return (str(url) if url else None, int(pid) if pid else None)
    except (FileNotFoundError, TypeError, ValueError, json.JSONDecodeError):
        return None, None


def main() -> int:
    args = _parser().parse_args()
    if args.command == "up":
        sandbox = DockerSandbox(_config(args))
        try:
            sandbox.start()
            project_root = Path(__file__).resolve().parents[2]
            dashboard = DashboardLauncher(project_root).start(sandbox.viewer_url, sandbox.api_url)
        except BaseException:
            sandbox.stop()
            raise
        _write_state(sandbox, dashboard)
        print(f"Dashboard URL: {dashboard.url}")
        print(f"Viewer URL: {sandbox.viewer_url}")
        print(f"API URL: {sandbox.api_url}")
        return 0
    if args.command == "down":
        _, dashboard_pid = _dashboard_state()
        try:
            sandbox = _load_sandbox()
        except RuntimeError:
            sandbox = DockerSandbox(_config(args))
        sandbox.stop()
        DashboardLauncher.stop(dashboard_pid)
        STATE_FILE.unlink(missing_ok=True)
        print("Friday sandbox removed.")
        return 0
    try:
        if args.command == "locate":
            return _locate(args)
        sandbox = _load_sandbox()
        if args.command == "status":
            sandbox.wait_until_ready()
            dashboard_url, _ = _dashboard_state()
            print(
                f"running and healthy\nDashboard URL: {dashboard_url or 'not running'}\n"
                f"Viewer URL: {sandbox.viewer_url}\nAPI URL: {sandbox.api_url}"
            )
            return 0
        if args.command == "act":
            return _act(args, sandbox)
        if args.command == "operation":
            return _operation(args, sandbox)
        with DesktopClient(sandbox, timeout=sandbox.config.request_timeout) as desktop:
            args.output.write_bytes(desktop.screenshot())
        print(f"Screenshot saved to {args.output}")
        return 0
    except (
        DesktopError,
        LLMError,
        OSError,
        TimeoutError,
        RuntimeError,
        ValidationError,
        ValueError,
    ) as error:
        print(f"Friday: {error}")
        return 1


def _locate(args: argparse.Namespace) -> int:
    if args.live:
        sandbox = _load_sandbox()
        with DesktopClient(sandbox, timeout=sandbox.config.request_timeout) as desktop:
            png = desktop.screenshot()
    else:
        png = args.image.read_bytes()
    settings = LLMSettings.from_env()
    llm = create_llm(settings)
    result = LocateRunner(
        llm,
        coordinate_grid=settings.coordinate_grid,
        max_retries=settings.max_retries,
    ).locate(png, args.instruction)
    if args.annotate:
        args.annotate.write_bytes(annotate_crosshair(png, *result.pixel))
    print(f"Normalized point: {result.normalized}")
    print(f"Pixel point: {result.pixel}")
    print(f"Image size: {result.image_size}")
    print(f"Raw model text: {result.raw_text}")
    return 0


def _act(args: argparse.Namespace, sandbox: DockerSandbox) -> int:
    action = parse_action(args.payload)
    with DesktopClient(sandbox, timeout=sandbox.config.request_timeout) as client:
        result = RemoteExecutor(client).execute(action)
        if args.screenshot:
            args.screenshot.write_bytes(result.image_png or client.screenshot())
    detail = f": {result.detail}" if result.detail else ""
    print(f"{action.action}: {'ok' if result.ok else 'failed'}{detail}")
    if result.point:
        print(f"Point: {result.point[0]}, {result.point[1]}")
    if args.screenshot:
        print(f"Screenshot saved to {args.screenshot}")
    return 0


def _operation(args: argparse.Namespace, sandbox: DockerSandbox) -> int:
    payload = json.loads(args.payload)
    with DesktopClient(sandbox, timeout=sandbox.config.request_timeout) as client:
        operation = parse_operation(payload, Path("/config/friday-workspace"))
        result = client.operation(operation)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
