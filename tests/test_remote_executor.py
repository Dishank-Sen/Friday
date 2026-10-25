from __future__ import annotations

from io import BytesIO

from PIL import Image

from friday.actions.models import MouseMoveAction, TypeAction, ZoomAction
from friday.desktop.client import DesktopClient
from friday.executor.remote import RemoteExecutor
from friday.sandbox.base import Sandbox
from friday.secrets import SecretValue


def _png() -> bytes:
    image = Image.new("RGB", (100, 80), "white")
    output = BytesIO()
    image.save(output, "PNG")
    return output.getvalue()


class FakeClient:
    def __init__(self) -> None:
        self.sent = []
        self.ops = []
        self.last_timeout: float | None = None

    def screenshot(self) -> bytes:
        return _png()

    def execute(self, action: object, timeout: float | None = None):
        self.sent.append(action)
        self.last_timeout = timeout
        from friday.actions.models import ActionResult

        return ActionResult(ok=True)

    def operation(self, operation: object):
        self.ops.append(operation)
        return {"ok": True, "pid": 42}


class FakeSandbox(Sandbox):
    @property
    def api_url(self) -> str:
        return "http://desktop.test"

    @property
    def viewer_url(self) -> str:
        return "http://viewer.test"

    @property
    def token(self) -> str:
        return "secret"

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def wait_until_ready(self) -> None:
        pass


def test_remote_executor_dispatches_action() -> None:
    client = FakeClient()
    executor = RemoteExecutor(client)  # type: ignore[arg-type]
    action = MouseMoveAction(action="mouse_move", x=2, y=3)

    assert executor.execute(action).ok
    assert client.sent == [action]


def test_remote_executor_passes_action_timeout_to_client() -> None:
    client = FakeClient()
    executor = RemoteExecutor(client)  # type: ignore[arg-type]
    action = TypeAction(action="type", text="x" * 500)

    executor.execute(action)

    # a long type has a budget > the default; assert a per-action timeout flowed
    assert client.last_timeout is not None
    assert client.last_timeout > 10.0


def test_remote_executor_posts_to_mocked_server() -> None:
    import httpx

    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"ok": True})

    with DesktopClient(FakeSandbox(), transport=httpx.MockTransport(handler)) as client:
        result = RemoteExecutor(client).execute(MouseMoveAction(action="mouse_move", x=2, y=3))

    assert result.ok
    assert seen[0].url.path == "/action"
    assert seen[0].headers["authorization"] == "Bearer secret"
    assert seen[0].content == b'{"action":"mouse_move","x":2,"y":3,"duration":0.0}'


def test_zoom_clamps_crop_and_maps_coordinates() -> None:
    executor = RemoteExecutor(FakeClient())  # type: ignore[arg-type]
    result = executor.execute(ZoomAction(action="zoom", factor=2, x=0, y=0))

    assert result.zoom is not None
    assert result.zoom.crop == (0, 0, 50, 40)
    assert result.zoom.to_screen(0, 0) == (0, 0)
    assert result.zoom.to_screen(98, 78) == (49, 39)


def test_remote_executor_dispatches_operation_to_client() -> None:
    from friday.harness.config import WORKSPACE_ROOT
    from friday.operations.registry import OpenUrl, parse_operation

    client = FakeClient()
    executor = RemoteExecutor(client)  # type: ignore[arg-type]
    operation = parse_operation(
        {"operation": "open_url", "url": "https://github.com/Dishank-Sen"}, WORKSPACE_ROOT
    )

    result = executor.execute(operation)

    assert isinstance(operation, OpenUrl)
    # an operation is routed to client.operation(), not client.execute()
    assert client.ops == [operation]
    assert client.sent == []
    assert result == {"ok": True, "pid": 42}


# --- type_secret: resolve by name from a vault and send VALUE only to the
# --- dedicated /type_secret path (never through the generic action dispatch)


class _Vault:
    def __init__(self, entries: dict[str, str]) -> None:
        self._entries = {name: SecretValue(value) for name, value in entries.items()}

    def contains(self, name: str) -> bool:
        return name in self._entries

    def get(self, name: str) -> SecretValue | None:
        return self._entries.get(name)


class FakeSecretClient(FakeClient):
    def __init__(self) -> None:
        super().__init__()
        self.secret_typed: list[tuple[str, str]] = []  # (name, value)

    def type_secret(self, name: str, value: str) -> None:
        self.secret_typed.append((name, value))


def test_remote_executor_types_a_secret_by_name_from_the_vault() -> None:
    from friday.actions.models import TypeSecretAction

    client = FakeSecretClient()
    vault = _Vault({"db_password": "hunter2"})
    executor = RemoteExecutor(client, secrets=vault)  # type: ignore[arg-type]
    action = TypeSecretAction(action="type_secret", name="db_password")

    result = executor.execute(action)

    assert result.ok
    # value went to the secret path, not the generic action dispatch
    assert client.secret_typed == [("db_password", "hunter2")]
    assert client.sent == []


def test_remote_executor_rejects_an_unknown_secret_name_without_typing() -> None:
    from friday.actions.models import TypeSecretAction

    client = FakeSecretClient()
    vault = _Vault({"db_password": "hunter2"})
    executor = RemoteExecutor(client, secrets=vault)  # type: ignore[arg-type]
    action = TypeSecretAction(action="type_secret", name="nope")

    result = executor.execute(action)

    assert result.ok is False
    assert client.secret_typed == []
    assert client.sent == []


def test_remote_executor_without_a_vault_rejects_secret_typing() -> None:
    from friday.actions.models import TypeSecretAction

    client = FakeSecretClient()
    executor = RemoteExecutor(client)  # no vault
    action = TypeSecretAction(action="type_secret", name="db_password")

    result = executor.execute(action)

    assert result.ok is False
    assert client.secret_typed == []
    assert client.sent == []
