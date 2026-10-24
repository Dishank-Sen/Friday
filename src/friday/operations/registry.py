"""Authoritative definitions for non-input desktop operations."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, get_args
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

WINDOW_ID = re.compile(r"^0x[0-9a-f]+$")
PROCESS_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")


class OperationError(ValueError):
    """An operation cannot be safely executed."""


class Operation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation: str


class _UrlOperation(Operation):
    url: str

    @field_validator("url")
    @classmethod
    def valid_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("url must use http or https and include a host")
        return value


class _PathOperation(Operation):
    path: str

    @field_validator("path")
    @classmethod
    def valid_path(cls, value: str, info: ValidationInfo) -> str:
        candidate = Path(value)
        if ".." in candidate.parts:
            raise ValueError("path must not contain '..'")
        workspace = info.context.get("workspace") if info.context else None
        if workspace:
            root = Path(workspace).resolve()
            resolved = (
                (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
            )
            try:
                resolved.relative_to(root)
            except ValueError as error:
                raise ValueError("path must stay inside the configured workspace") from error
        return value


class LaunchApp(Operation):
    operation: Literal["launch_app"]
    app: Literal["browser", "terminal", "file_manager", "text_editor"]
    args: list[str] = Field(default_factory=list, max_length=20)


class OpenUrl(_UrlOperation):
    operation: Literal["open_url"]


class OpenTerminalIn(_PathOperation):
    operation: Literal["open_terminal_in"]


class OpenFileManager(_PathOperation):
    operation: Literal["open_file_manager"]


class OpenFile(_PathOperation):
    operation: Literal["open_file"]


class LaunchBrowserDebug(_UrlOperation):
    operation: Literal["launch_browser_debug"]


class ListWindows(Operation):
    operation: Literal["list_windows"]


class ActiveWindow(Operation):
    operation: Literal["active_window"]


class _WindowOperation(Operation):
    window_id: str

    @field_validator("window_id")
    @classmethod
    def valid_window_id(cls, value: str) -> str:
        if not WINDOW_ID.fullmatch(value):
            raise ValueError("window_id must match ^0x[0-9a-f]+$")
        return value


class FocusWindow(_WindowOperation):
    operation: Literal["focus_window"]


class CloseWindow(_WindowOperation):
    operation: Literal["close_window"]


class MinimizeWindow(_WindowOperation):
    operation: Literal["minimize_window"]


class MaximizeWindow(_WindowOperation):
    operation: Literal["maximize_window"]


class MoveResizeWindow(_WindowOperation):
    operation: Literal["move_resize_window"]
    x: int
    y: int
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class WaitForWindow(Operation):
    operation: Literal["wait_for_window"]
    title: str = Field(min_length=1, max_length=200)
    timeout: float = Field(default=5.0, gt=0, le=30)


class SetClipboard(Operation):
    operation: Literal["set_clipboard"]
    text: str = Field(max_length=100_000)


class GetClipboard(Operation):
    operation: Literal["get_clipboard"]


class IsRunning(Operation):
    operation: Literal["is_running"]
    name: str

    @field_validator("name")
    @classmethod
    def valid_name(cls, value: str) -> str:
        if not PROCESS_NAME.fullmatch(value):
            raise ValueError("process name contains invalid characters")
        return value


class ListProcesses(Operation):
    operation: Literal["list_processes"]


class CloseApp(Operation):
    operation: Literal["close_app"]
    pid: int = Field(gt=0)


class ReadFile(_PathOperation):
    operation: Literal["read_file"]


class WriteFile(_PathOperation):
    operation: Literal["write_file"]
    content: str = Field(max_length=1_000_000)


class ListDir(_PathOperation):
    operation: Literal["list_dir"]


class MakeDir(_PathOperation):
    operation: Literal["make_dir"]


class DeleteFile(_PathOperation):
    operation: Literal["delete_file"]


SystemOperation = (
    LaunchApp
    | OpenUrl
    | OpenTerminalIn
    | OpenFileManager
    | OpenFile
    | LaunchBrowserDebug
    | ListWindows
    | ActiveWindow
    | FocusWindow
    | CloseWindow
    | MinimizeWindow
    | MaximizeWindow
    | MoveResizeWindow
    | WaitForWindow
    | SetClipboard
    | GetClipboard
    | IsRunning
    | ListProcesses
    | CloseApp
    | ReadFile
    | WriteFile
    | ListDir
    | MakeDir
    | DeleteFile
)

ArgvBuilder = Callable[[SystemOperation, Path], list[str] | None]


@dataclass(frozen=True, slots=True)
class OperationDefinition:
    name: str
    category: str
    description: str
    model: type[Operation]
    argv: str
    timeout: float
    side_effects: str
    security: str
    builder: ArgvBuilder


def _path(value: str, workspace: Path) -> str:
    return str(
        (workspace / value).resolve() if not Path(value).is_absolute() else Path(value).resolve()
    )


APP_ARGV = {
    "browser": ["chromium"],
    "terminal": ["xfce4-terminal"],
    "file_manager": ["thunar"],
    "text_editor": ["mousepad"],
}


def _argv(op: SystemOperation, workspace: Path) -> list[str] | None:
    match op:
        case LaunchApp(app=app, args=args):
            return [*APP_ARGV[app], *args]
        case OpenUrl(url=url):
            return ["chromium", url]
        case OpenTerminalIn(path=path):
            return ["xfce4-terminal", "--working-directory", _path(path, workspace)]
        case OpenFileManager(path=path):
            return ["thunar", _path(path, workspace)]
        case OpenFile(path=path):
            return ["xdg-open", _path(path, workspace)]
        case LaunchBrowserDebug(url=url):
            return [
                "chromium",
                "--remote-debugging-port=9222",
                "--user-data-dir=/tmp/friday-chromium-debug",
                url,
            ]
        case ListWindows():
            return ["wmctrl", "-lpG"]
        case ActiveWindow():
            return ["xdotool", "getactivewindow", "getwindowname"]
        case FocusWindow(window_id=wid):
            return ["wmctrl", "-i", "-a", wid]
        case CloseWindow(window_id=wid):
            return ["wmctrl", "-i", "-c", wid]
        case MinimizeWindow(window_id=wid):
            return ["xdotool", "windowminimize", wid]
        case MaximizeWindow(window_id=wid):
            return ["wmctrl", "-i", "-r", wid, "-b", "add,maximized_vert,maximized_horz"]
        case MoveResizeWindow(window_id=wid, x=x, y=y, width=w, height=h):
            return ["wmctrl", "-i", "-r", wid, "-e", f"0,{x},{y},{w},{h}"]
        case WaitForWindow(title=title):
            return ["xdotool", "search", "--sync", "--onlyvisible", "--name", title]
        case SetClipboard():
            return ["xclip", "-selection", "clipboard"]
        case GetClipboard():
            return ["xclip", "-selection", "clipboard", "-o"]
        case IsRunning(name=name):
            return ["pgrep", "-x", name]
        case ListProcesses():
            return ["ps", "-eo", "pid,comm"]
        case _:
            return None


_MODELS = {
    get_args(cls.model_fields["operation"].annotation)[0]: cls for cls in SystemOperation.__args__
}


def parse_operation(payload: dict[str, Any], workspace: Path) -> SystemOperation:
    name = payload.get("operation")
    if not isinstance(name, str) or name not in _MODELS:
        raise OperationError("unknown operation")
    return _MODELS[name].model_validate(payload, context={"workspace": workspace})


def _definition(
    name: str, category: str, model: type[Operation], argv: str, side: str
) -> OperationDefinition:
    return OperationDefinition(
        name,
        category,
        name.replace("_", " "),
        model,
        argv,
        10,
        side,
        "validated before execution",
        _argv,
    )


OPERATIONS = {
    name: _definition(name, category, model, argv, side)
    for name, category, model, argv, side in [
        ("launch_app", "launch", LaunchApp, "allowlisted binary + args", "starts an app"),
        ("open_url", "launch", OpenUrl, "chromium <url>", "opens URL"),
        (
            "open_terminal_in",
            "launch",
            OpenTerminalIn,
            "xfce4-terminal --working-directory <path>",
            "opens terminal",
        ),
        ("open_file_manager", "launch", OpenFileManager, "thunar <path>", "opens file manager"),
        ("open_file", "launch", OpenFile, "xdg-open <path>", "opens file"),
        (
            "launch_browser_debug",
            "launch",
            LaunchBrowserDebug,
            "chromium --remote-debugging-port=9222 "
            "--user-data-dir=/tmp/friday-chromium-debug <url>",
            "starts debug browser",
        ),
        ("list_windows", "windows", ListWindows, "wmctrl -lpG", "none"),
        ("active_window", "windows", ActiveWindow, "xdotool getactivewindow getwindowname", "none"),
        ("focus_window", "windows", FocusWindow, "wmctrl -i -a <id>", "changes focus"),
        ("close_window", "windows", CloseWindow, "wmctrl -i -c <id>", "closes window"),
        ("minimize_window", "windows", MinimizeWindow, "xdotool windowminimize <id>", "minimizes"),
        (
            "maximize_window",
            "windows",
            MaximizeWindow,
            "wmctrl -i -r <id> -b add,maximized_vert,maximized_horz",
            "maximizes",
        ),
        (
            "move_resize_window",
            "windows",
            MoveResizeWindow,
            "wmctrl -i -r <id> -e 0,x,y,w,h",
            "moves window",
        ),
        (
            "wait_for_window",
            "windows",
            WaitForWindow,
            "xdotool search --sync --onlyvisible --name <title>",
            "waits",
        ),
        (
            "set_clipboard",
            "clipboard",
            SetClipboard,
            "xclip -selection clipboard",
            "changes clipboard",
        ),
        ("get_clipboard", "clipboard", GetClipboard, "xclip -selection clipboard -o", "none"),
        ("is_running", "processes", IsRunning, "pgrep -x <name>", "none"),
        ("list_processes", "processes", ListProcesses, "ps -eo pid,comm", "none"),
        ("close_app", "processes", CloseApp, "SIGTERM tracked pid", "terminates launched app"),
        ("read_file", "files", ReadFile, "pathlib.Path.read_text", "none"),
        ("write_file", "files", WriteFile, "pathlib.Path.write_text", "writes file"),
        ("list_dir", "files", ListDir, "pathlib.Path.iterdir", "none"),
        ("make_dir", "files", MakeDir, "pathlib.Path.mkdir", "creates directory"),
        ("delete_file", "files", DeleteFile, "pathlib.Path.unlink/rmtree", "deletes file"),
    ]
}
