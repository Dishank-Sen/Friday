"""Executor that dispatches typed actions and system operations through the control API."""

from __future__ import annotations

from typing import Protocol

from friday.actions.config import timeout_for
from friday.actions.models import Action, ActionResult, TypeSecretAction, ZoomAction
from friday.desktop.client import DesktopClient
from friday.operations.registry import SystemOperation
from friday.secrets import SecretValue as _SecretValue  # type-annotate only

from .zoom import zoom_image

Payload = Action | SystemOperation


class Vault(Protocol):
    def contains(self, name: str) -> bool: ...
    def get(self, name: str) -> _SecretValue | None: ...


class Executor(Protocol):
    def execute(self, payload: Payload) -> ActionResult | dict: ...


class RemoteExecutor:
    def __init__(self, client: DesktopClient, secrets: Vault | None = None) -> None:
        self._client = client
        self._secrets = secrets

    def execute(self, payload: Payload) -> ActionResult | dict:
        if isinstance(payload, ZoomAction):
            view = zoom_image(self._client.screenshot(), payload.factor, payload.x, payload.y)
            return ActionResult(ok=True, image_png=view.image_png, zoom=view)
        if isinstance(payload, TypeSecretAction):
            return self._type_secret(payload)
        operation = getattr(payload, "operation", None)
        if operation is not None:
            return self._client.operation(payload)
        return self._client.execute(payload, timeout=timeout_for(payload))

    def _type_secret(self, payload: TypeSecretAction) -> ActionResult:
        """Resolve a secret by name and type it through the secret-only path.

        The value is unwrapped here (the single deliberate typing gate) and
        passed only to ``client.type_secret``, which sends it solely to the
        dedicated secret endpoint on stdin. It never enters the generic action
        dispatch, state, or detail.
        """
        if self._secrets is None or not self._secrets.contains(payload.name):
            return ActionResult(ok=False, detail=f"unknown secret name: {payload.name}")
        secret = self._secrets.get(payload.name)
        if secret is None:
            return ActionResult(ok=False, detail=f"unknown secret name: {payload.name}")
        from friday.secrets import unwrap

        self._client.type_secret(payload.name, unwrap(secret))
        return ActionResult(ok=True, detail="secret typed")
