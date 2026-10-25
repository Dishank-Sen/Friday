from __future__ import annotations

import base64
import json
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    TypeAdapter,
    field_serializer,
    field_validator,
    model_validator,
)

from friday.shortcuts.registry import shortcut_definition

from .config import (
    MAX_HOLD_SECONDS,
    MAX_MOUSE_MOVE_SECONDS,
    MAX_SCROLL_AMOUNT,
    MAX_TEXT_LENGTH,
    MAX_WAIT_SECONDS,
    MAX_ZOOM_FACTOR,
    MIN_ZOOM_FACTOR,
)
from .keys import normalize_key


class _Action(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LeftClickAction(_Action):
    action: Literal["left_click"]
    x: StrictInt
    y: StrictInt


class RightClickAction(_Action):
    action: Literal["right_click"]
    x: StrictInt
    y: StrictInt


class MiddleClickAction(_Action):
    action: Literal["middle_click"]
    x: StrictInt
    y: StrictInt


class DoubleClickAction(_Action):
    action: Literal["double_click"]
    x: StrictInt
    y: StrictInt


class TripleClickAction(_Action):
    action: Literal["triple_click"]
    x: StrictInt
    y: StrictInt


class LeftClickDragAction(_Action):
    action: Literal["left_click_drag"]
    start_x: StrictInt
    start_y: StrictInt
    end_x: StrictInt
    end_y: StrictInt


class MouseMoveAction(_Action):
    action: Literal["mouse_move"]
    x: StrictInt
    y: StrictInt
    duration: float = Field(default=0.0, ge=0, le=MAX_MOUSE_MOVE_SECONDS)


class LeftMouseDownAction(_Action):
    action: Literal["left_mouse_down"]


class LeftMouseUpAction(_Action):
    action: Literal["left_mouse_up"]


class ScrollAction(_Action):
    action: Literal["scroll"]
    amount: StrictInt = Field(ge=-MAX_SCROLL_AMOUNT, le=MAX_SCROLL_AMOUNT)
    x: StrictInt | None = None
    y: StrictInt | None = None
    horizontal: bool = False

    @model_validator(mode="after")
    def _validate_scroll(self) -> ScrollAction:
        if self.amount == 0:
            raise ValueError("scroll amount cannot be zero")
        if (self.x is None) != (self.y is None):
            raise ValueError("scroll x and y must be provided together")
        return self


class TypeAction(_Action):
    action: Literal["type"]
    text: str = Field(max_length=MAX_TEXT_LENGTH)


# A secret is referenced by NAME ONLY. The value is never part of the action,
# its serialized form, or any prompt/state — it is resolved from the vault and
# typed at execution time (see the executor secrets layer).
MAX_SECRET_NAME_LENGTH = 128


class TypeSecretAction(_Action):
    action: Literal["type_secret"]
    name: str = Field(min_length=1, max_length=MAX_SECRET_NAME_LENGTH)

    @field_validator("name")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("secret name must not be blank")
        return value


class KeyAction(_Action):
    action: Literal["key"]
    key: str

    @field_validator("key")
    @classmethod
    def _validate_key(cls, value: str) -> str:
        return normalize_key(value)


class HoldKeyAction(_Action):
    action: Literal["hold_key"]
    key: str
    duration: float = Field(gt=0, le=MAX_HOLD_SECONDS)

    @field_validator("key")
    @classmethod
    def _validate_key(cls, value: str) -> str:
        return normalize_key(value)


class ShortcutAction(_Action):
    action: Literal["shortcut"]
    name: str
    repeat: int = Field(default=1, ge=1, le=10)

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        shortcut_definition(value)
        return value


class WaitAction(_Action):
    action: Literal["wait"]
    seconds: float = Field(default=1.0, gt=0, le=MAX_WAIT_SECONDS)


class ScreenshotAction(_Action):
    action: Literal["screenshot"]


class CursorPositionAction(_Action):
    action: Literal["cursor_position"]


class ZoomAction(_Action):
    action: Literal["zoom"]
    factor: float = Field(ge=MIN_ZOOM_FACTOR, le=MAX_ZOOM_FACTOR)
    x: StrictInt
    y: StrictInt


Action = Annotated[
    (
        LeftClickAction
        | RightClickAction
        | MiddleClickAction
        | DoubleClickAction
        | TripleClickAction
        | LeftClickDragAction
        | MouseMoveAction
        | LeftMouseDownAction
        | LeftMouseUpAction
        | ScrollAction
        | TypeAction
        | TypeSecretAction
        | KeyAction
        | HoldKeyAction
        | ShortcutAction
        | WaitAction
        | ScreenshotAction
        | CursorPositionAction
        | ZoomAction
    ),
    Field(discriminator="action"),
]
ACTION_ADAPTER = TypeAdapter(Action)


class ActionResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    ok: bool
    detail: str | None = None
    image_png: bytes | None = None
    point: tuple[int, int] | None = None
    zoom: Any | None = None

    @field_serializer("image_png", when_used="json")
    def _serialize_image(self, image: bytes | None) -> str | None:
        return None if image is None else base64.b64encode(image).decode("ascii")

    @field_validator("image_png", mode="before")
    @classmethod
    def _deserialize_image(cls, image: object) -> object:
        if isinstance(image, str):
            return base64.b64decode(image, validate=True)
        return image


def parse_action(payload: str | dict[str, object]) -> Action:
    data = json.loads(payload) if isinstance(payload, str) else payload
    return ACTION_ADAPTER.validate_python(data)
