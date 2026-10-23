"""Docker implementation of the sandbox interface."""

from __future__ import annotations

import logging
import secrets
import socket
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

import docker
from docker.errors import APIError, ImageNotFound, NotFound

from friday.config import FridayConfig
from friday.constants import CONTROL_CONTAINER_PORT, WEBTOP_CONTAINER_PORT

from .base import Sandbox

LOGGER = logging.getLogger(__name__)


class DockerSandbox(Sandbox):
    def __init__(self, config: FridayConfig | None = None, client: docker.DockerClient | None = None) -> None:
        self.config = config or FridayConfig()
        self._client = client or docker.from_env()
        self._container: Any | None = None
        self._viewer_port: int | None = None
        self._api_port: int | None = None
        self._token = secrets.token_urlsafe(32)

    @classmethod
    def from_existing(
        cls,
        config: FridayConfig,
        *,
        viewer_port: int,
        api_port: int,
        token: str,
        client: docker.DockerClient | None = None,
    ) -> "DockerSandbox":
        sandbox = cls(config, client)
        sandbox._viewer_port = viewer_port
        sandbox._api_port = api_port
        sandbox._token = token
        return sandbox

    @property
    def api_url(self) -> str:
        if self._api_port is None:
            raise RuntimeError("sandbox has not started")
        return f"http://127.0.0.1:{self._api_port}"

    @property
    def viewer_url(self) -> str:
        if self._viewer_port is None:
            raise RuntimeError("sandbox has not started")
        return f"http://127.0.0.1:{self._viewer_port}"

    @property
    def token(self) -> str:
        return self._token

    def start(self) -> None:
        self._ensure_image()
        self._replace_existing_container()
        self._viewer_port = self._pick_port(self.config.viewer_port)
        self._api_port = self._pick_port(self.config.api_port, reserved={self._viewer_port})
        environment = {
            "FRIDAY_CONTROL_TOKEN": self._token,
            "PIXELFLUX_WAYLAND": "false",
            "SELKIES_MANUAL_WIDTH": str(self.config.width),
            "SELKIES_MANUAL_HEIGHT": str(self.config.height),
        }
        ports = {
            f"{WEBTOP_CONTAINER_PORT}/tcp": ("127.0.0.1", self._viewer_port),
            f"{CONTROL_CONTAINER_PORT}/tcp": ("127.0.0.1", self._api_port),
        }
        try:
            self._container = self._client.containers.run(
                self.config.image,
                name=self.config.container_name,
                detach=True,
                environment=environment,
                ports=ports,
                shm_size=self.config.shm_size,
                labels={"io.friday.managed": "true"},
            )
            self.wait_until_ready()
        except BaseException as error:
            logs = self._logs()
            self.stop()
            if isinstance(error, KeyboardInterrupt):
                raise
            raise RuntimeError(f"Friday sandbox failed to start. Container logs:\n{logs}") from None

    def stop(self) -> None:
        container = self._container
        if container is None:
            try:
                container = self._client.containers.get(self.config.container_name)
            except NotFound:
                return
        try:
            container.remove(force=True)
        except (NotFound, APIError):
            LOGGER.warning("could not remove container %s", self.config.container_name, exc_info=True)
        finally:
            self._container = None
            self._viewer_port = None
            self._api_port = None

    def wait_until_ready(self) -> None:
        deadline = time.monotonic() + self.config.startup_timeout
        health_url = f"{self.api_url}/health"
        while time.monotonic() < deadline:
            try:
                with urlopen(health_url, timeout=self.config.request_timeout) as response:  # noqa: S310
                    if response.status == 200:
                        return
            except (OSError, URLError):
                time.sleep(0.25)
        raise TimeoutError(f"control server did not become healthy within {self.config.startup_timeout}s")

    def _ensure_image(self) -> None:
        try:
            self._client.images.get(self.config.image)
            if not self.config.rebuild_image:
                return
        except ImageNotFound:
            pass
        project_root = Path(__file__).resolve().parents[3]
        LOGGER.info("building image %s", self.config.image)
        self._client.images.build(
            path=str(project_root),
            dockerfile="docker/Dockerfile",
            tag=self.config.image,
            rm=True,
        )

    def _replace_existing_container(self) -> None:
        try:
            existing = self._client.containers.get(self.config.container_name)
        except NotFound:
            return
        LOGGER.info("replacing existing container %s", self.config.container_name)
        existing.remove(force=True)

    @staticmethod
    def _pick_port(requested: int | None, reserved: set[int | None] | None = None) -> int:
        reserved = reserved or set()
        if requested is not None and requested not in reserved and DockerSandbox._can_bind(requested):
            return requested
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", 0))
            port = int(probe.getsockname()[1])
        if port in reserved:
            return DockerSandbox._pick_port(None, reserved)
        return port

    @staticmethod
    def _can_bind(port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                probe.bind(("127.0.0.1", port))
        except OSError:
            return False
        return True

    def _logs(self) -> str:
        if self._container is None:
            return "container was not created"
        try:
            return self._container.logs(tail=200).decode(errors="replace")
        except APIError:
            return "could not retrieve container logs"
