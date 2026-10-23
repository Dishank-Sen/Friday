"""Configuration for the Friday desktop sandbox."""

from __future__ import annotations

from dataclasses import dataclass

from .constants import DEFAULT_CONTAINER_NAME, DEFAULT_IMAGE


@dataclass(frozen=True, slots=True)
class FridayConfig:
    image: str = DEFAULT_IMAGE
    container_name: str = DEFAULT_CONTAINER_NAME
    viewer_port: int | None = None
    api_port: int | None = None
    width: int = 1280
    height: int = 720
    shm_size: str = "1g"
    token: str | None = None
    startup_timeout: float = 45.0
    request_timeout: float = 10.0
    rebuild_image: bool = False

    def __post_init__(self) -> None:
        if self.viewer_port is not None and not 1 <= self.viewer_port <= 65535:
            raise ValueError("viewer_port must be between 1 and 65535")
        if self.api_port is not None and not 1 <= self.api_port <= 65535:
            raise ValueError("api_port must be between 1 and 65535")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be positive")
        if self.startup_timeout <= 0 or self.request_timeout <= 0:
            raise ValueError("timeouts must be positive")
