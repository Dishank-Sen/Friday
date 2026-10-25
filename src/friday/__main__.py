"""Command-line entry point for Friday."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path

from pydantic import ValidationError

from friday.actions.focus import focused_app_for
from friday.actions.models import parse_action
from friday.config import FridayConfig
from friday.dashboard import Dashboard, DashboardLauncher
from friday.desktop.client import DesktopClient
from friday.desktop.errors import DesktopError
from friday.executor.remote import RemoteExecutor
from friday.graph.locate import LocateRunner
from friday.harness.capabilities import ControlPolicy
from friday.harness.compose import ProductionDeps, build_production_graph
from friday.harness.nodes.executor import ExecutorDeps, make_executor_node
from friday.harness.nodes.guard import make_guard
from friday.harness.nodes.observe import make_observe
from friday.harness.state import initial_state
from friday.harness.steps import ExecutorSettings
from friday.harness.trace import ObservationTraceWriter
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
    up = subparsers.add_parser("up")
    up.add_argument(
        "--rebuild", action="store_true", help="rebuild the sandbox image before starting"
    )
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
    run_cmd = subparsers.add_parser(
        "run", help="observe, build context, and ask the model for the next decision"
    )
    run_cmd.add_argument("goal", help="task/prompt to decide on")
    run_cmd.add_argument("--trace-dir", type=Path, default=Path(".friday-traces"))
    exec_once = subparsers.add_parser(
        "exec-once", help="run the real guard then executor against a live sandbox"
    )
    exec_once.add_argument("action", help="JSON action object to execute if guard allows")
    exec_once.add_argument("--trace-dir", type=Path, default=Path(".friday-traces"))
    return parser


def _config(args: argparse.Namespace) -> FridayConfig:
    return FridayConfig(
        image=args.docker_image,
        container_name=args.name,
        viewer_port=args.viewer_port,
        api_port=args.api_port,
        width=args.width,
        height=args.height,
        rebuild_image=bool(getattr(args, "rebuild", False)),
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
        if args.command == "run":
            return _run_task(args)
        if args.command == "exec-once":
            return _exec_once(args)
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


def _run_task(args: argparse.Namespace) -> int:
    """Run the harness through the production graph up to decide, print decide output.

    A live sandbox is required (``python -m friday up`` first). The graph
    ``build_production_graph`` assembles the real observe, build_context, decide,
    and guard nodes; the run goes observe -> build_context -> decide and prints
    the model's decision. Only the decision is printed; nothing executes.
    """
    sandbox = _load_sandbox()
    settings = LLMSettings.from_env()
    llm = create_llm(settings)
    max_steps = max(1, settings.max_retries + 10)

    state = initial_state(args.goal, max_steps)
    state["started_at"] = time.time()
    with DesktopClient(sandbox, timeout=sandbox.config.request_timeout) as desktop:
        deps = ProductionDeps(
            client=desktop,
            trace_writer=ObservationTraceWriter(args.trace_dir),
            focus_table=focused_app_for,
            llm=llm,
            policy=_CliPolicy(),
        )
        graph = build_production_graph(deps)
        result = graph.invoke(state)

    print("=== decide output ===")
    for key in ("decision", "pending_action", "retries"):
        if result.get(key) is not None:
            print(f"{key}: {json.dumps(result[key], sort_keys=True)}")
    if result.get("status") == "failed":
        print(f"observation failed: {result.get('final_report')}")
        return 1
    return 0


class _CliPolicy:
    """A permissive policy so a plain `run` can exercise the decide path."""

    def policy(self, state):  # noqa: ANN001, ANN201
        return ControlPolicy(approval=True, user_control=False)


def _exec_once(args: argparse.Namespace, print=print) -> int:
    """Run the real guard then executor on one action, with no model or graph.

    Builds state from a real observation (the observe node), evaluates the real
    guard, and only if it allows, runs the real executor node. Prints the
    verdict/hint, the last_result, and where any observation image was saved.
    """
    try:
        action = parse_action(args.action)
    except (ValueError, TypeError) as error:
        print(f"Friday: invalid action: {error}")
        return 1

    sandbox = _load_sandbox()
    with DesktopClient(sandbox, timeout=sandbox.config.request_timeout) as desktop:
        state = initial_state("exec-once", 5)
        state["started_at"] = time.time()

        observe_node = make_observe(
            desktop, ObservationTraceWriter(args.trace_dir), focused_app_for
        )
        state.update(observe_node(state))
        state["pending_action"] = {"action": action.action}

        guard_node = make_guard(policy=_CliPolicy())
        verdict_update = guard_node(state)
        verdict = verdict_update.get("guard_verdict")
        hint = verdict_update.get("hint")
        print(f"guard verdict: {verdict}")
        if hint:
            print(f"guard hint: {hint}")

        if verdict != "allow":
            return 0

        state.update(verdict_update)
        state["guard_verdict"] = verdict
        executor_node = make_executor_node(
            ExecutorDeps(
                executor=RemoteExecutor(desktop),
                trace_writer=ObservationTraceWriter(args.trace_dir),
                settings=ExecutorSettings(),
            )
        )
        update = executor_node(state)
        last_result = update.get("last_result") or {}
        print("last_result: " + json.dumps(last_result, sort_keys=True))
        if last_result.get("image_path"):
            print(f"image saved: {last_result['image_path']}")
    return 0


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
