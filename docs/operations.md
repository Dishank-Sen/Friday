# Friday operations

## Overview and conventions

Coordinates are integer real-screen pixels. Operations use argv lists only; never shell strings. All server requests are Pydantic-validated before execution. URLs are limited to HTTP(S), window IDs use `^0x[0-9a-f]+$`, paths stay inside the configured workspace, and only Friday-started PIDs can be closed. Typed text, clipboard data, and file content must never be logged. Display work is serialized by one lock.

## Summary

| Operation | Category | Command |
| --- | --- | --- |
| `left_click` | input | `xdotool mousemove x y; xdotool click 1` |
| `right_click` | input | `xdotool mousemove x y; xdotool click 3` |
| `middle_click` | input | `xdotool mousemove x y; xdotool click 2` |
| `double_click` | input | `xdotool mousemove x y; xdotool click --repeat 2 --delay 100 1` |
| `triple_click` | input | `xdotool mousemove x y; xdotool click --repeat 3 --delay 100 1` |
| `left_click_drag` | input | `xdotool mousemove/mousedown/mouseup` |
| `mouse_move` | input | `xdotool mousemove x y` |
| `left_mouse_down` | input | `xdotool mousedown 1` |
| `left_mouse_up` | input | `xdotool mouseup 1` |
| `scroll` | input | `xdotool click 4/5/6/7` |
| `type` | input | `xdotool type --delay 20 -- text` |
| `key` | input | `xdotool key -- key` |
| `hold_key` | input | `xdotool keydown/keyup -- key` |
| `wait` | input | `Python time.sleep` |
| `screenshot` | observation | `scrot -- path` |
| `cursor_position` | observation | `xdotool getmouselocation --shell` |
| `screen_size` | observation | `xdotool getdisplaygeometry` |
| `zoom` | observation | `Pillow crop and resize` |
| `launch_app` | launch | `allowlisted binary + args` |
| `open_url` | launch | `chromium <url>` |
| `open_terminal_in` | launch | `xfce4-terminal --working-directory <path>` |
| `open_file_manager` | launch | `thunar <path>` |
| `open_file` | launch | `xdg-open <path>` |
| `launch_browser_debug` | launch | `chromium --remote-debugging-port=9222 --user-data-dir=/tmp/friday-chromium-debug <url>` |
| `list_windows` | windows | `wmctrl -lpG` |
| `active_window` | windows | `xdotool getactivewindow getwindowname` |
| `focus_window` | windows | `wmctrl -i -a <id>` |
| `close_window` | windows | `wmctrl -i -c <id>` |
| `minimize_window` | windows | `xdotool windowminimize <id>` |
| `maximize_window` | windows | `wmctrl -i -r <id> -b add,maximized_vert,maximized_horz` |
| `move_resize_window` | windows | `wmctrl -i -r <id> -e 0,x,y,w,h` |
| `wait_for_window` | windows | `xdotool search --sync --onlyvisible --name <title>` |
| `set_clipboard` | clipboard | `xclip -selection clipboard -loops 0` |
| `get_clipboard` | clipboard | `xclip -selection clipboard -o` |
| `is_running` | processes | `pgrep -x <name>` |
| `list_processes` | processes | `ps -eo pid,comm` |
| `close_app` | processes | `SIGTERM tracked pid` |
| `read_file` | files | `pathlib.Path.read_text` |
| `write_file` | files | `pathlib.Path.write_text` |
| `list_dir` | files | `pathlib.Path.iterdir` |
| `make_dir` | files | `pathlib.Path.mkdir` |
| `delete_file` | files | `pathlib.Path.unlink/rmtree` |
## `left_click`

- Category: input
- Description: left click
- Parameters: existing action model
- Command: `xdotool mousemove x y; xdotool click 1`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: unverified in this system-operations pass; existing executor behavior was not changed

## `right_click`

- Category: input
- Description: right click
- Parameters: existing action model
- Command: `xdotool mousemove x y; xdotool click 3`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: unverified in this system-operations pass; existing executor behavior was not changed

## `middle_click`

- Category: input
- Description: middle click
- Parameters: existing action model
- Command: `xdotool mousemove x y; xdotool click 2`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: unverified in this system-operations pass; existing executor behavior was not changed

## `double_click`

- Category: input
- Description: double click
- Parameters: existing action model
- Command: `xdotool mousemove x y; xdotool click --repeat 2 --delay 100 1`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: unverified in this system-operations pass; existing executor behavior was not changed

## `triple_click`

- Category: input
- Description: triple click
- Parameters: existing action model
- Command: `xdotool mousemove x y; xdotool click --repeat 3 --delay 100 1`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: unverified in this system-operations pass; existing executor behavior was not changed

## `left_click_drag`

- Category: input
- Description: interpolated left drag
- Parameters: existing action model
- Command: `xdotool mousemove/mousedown/mouseup`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: unverified in this system-operations pass; existing executor behavior was not changed

## `mouse_move`

- Category: input
- Description: move cursor
- Parameters: existing action model
- Command: `xdotool mousemove x y`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: unverified in this system-operations pass; existing executor behavior was not changed

## `left_mouse_down`

- Category: input
- Description: hold left button
- Parameters: existing action model
- Command: `xdotool mousedown 1`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: unverified in this system-operations pass; existing executor behavior was not changed

## `left_mouse_up`

- Category: input
- Description: release left button
- Parameters: existing action model
- Command: `xdotool mouseup 1`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: unverified in this system-operations pass; existing executor behavior was not changed

## `scroll`

- Category: input
- Description: scroll
- Parameters: existing action model
- Command: `xdotool click 4/5/6/7`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: unverified in this system-operations pass; existing executor behavior was not changed

## `type`

- Category: input
- Description: type text
- Parameters: existing action model
- Command: `xdotool type --delay 20 -- text`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: unverified in this system-operations pass; existing executor behavior was not changed

## `key`

- Category: input
- Description: send key
- Parameters: existing action model
- Command: `xdotool key -- key`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: unverified in this system-operations pass; existing executor behavior was not changed

## `hold_key`

- Category: input
- Description: hold key
- Parameters: existing action model
- Command: `xdotool keydown/keyup -- key`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: unverified in this system-operations pass; existing executor behavior was not changed

## `wait`

- Category: input
- Description: wait
- Parameters: existing action model
- Command: `Python time.sleep`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: unverified in this system-operations pass; existing executor behavior was not changed

## `screenshot`

- Category: observation
- Description: capture PNG
- Parameters: existing action model
- Command: `scrot -- path`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: unverified in this system-operations pass; existing executor behavior was not changed

## `cursor_position`

- Category: observation
- Description: read cursor
- Parameters: existing action model
- Command: `xdotool getmouselocation --shell`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: unverified in this system-operations pass; existing executor behavior was not changed

## `screen_size`

- Category: observation
- Description: read screen size
- Parameters: existing action model
- Command: `xdotool getdisplaygeometry`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: unverified in this system-operations pass; existing executor behavior was not changed

## `zoom`

- Category: observation
- Description: host-only zoom
- Parameters: existing action model
- Command: `Pillow crop and resize`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: unverified in this system-operations pass; existing executor behavior was not changed

## `launch_app`

- Category: launch
- Description: launch app
- Parameters: `app`: typing.Literal['browser', 'terminal', 'file_manager', 'text_editor'], `args`: list[str]
- Command: `allowlisted binary + args`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `open_url`

- Category: launch
- Description: open url
- Parameters: `url`: <class 'str'>
- Command: `chromium <url>`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `open_terminal_in`

- Category: launch
- Description: open terminal in
- Parameters: `path`: <class 'str'>
- Command: `xfce4-terminal --working-directory <path>`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `open_file_manager`

- Category: launch
- Description: open file manager
- Parameters: `path`: <class 'str'>
- Command: `thunar <path>`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `open_file`

- Category: launch
- Description: open file
- Parameters: `path`: <class 'str'>
- Command: `xdg-open <path>`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `launch_browser_debug`

- Category: launch
- Description: launch browser debug
- Parameters: `url`: <class 'str'>
- Command: `chromium --remote-debugging-port=9222 --user-data-dir=/tmp/friday-chromium-debug <url>`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `list_windows`

- Category: windows
- Description: list windows
- Parameters: none
- Command: `wmctrl -lpG`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `active_window`

- Category: windows
- Description: active window
- Parameters: none
- Command: `xdotool getactivewindow getwindowname`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `focus_window`

- Category: windows
- Description: focus window
- Parameters: `window_id`: <class 'str'>
- Command: `wmctrl -i -a <id>`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `close_window`

- Category: windows
- Description: close window
- Parameters: `window_id`: <class 'str'>
- Command: `wmctrl -i -c <id>`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `minimize_window`

- Category: windows
- Description: minimize window
- Parameters: `window_id`: <class 'str'>
- Command: `xdotool windowminimize <id>`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `maximize_window`

- Category: windows
- Description: maximize window
- Parameters: `window_id`: <class 'str'>
- Command: `wmctrl -i -r <id> -b add,maximized_vert,maximized_horz`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `move_resize_window`

- Category: windows
- Description: move resize window
- Parameters: `window_id`: <class 'str'>, `x`: <class 'int'>, `y`: <class 'int'>, `width`: <class 'int'>, `height`: <class 'int'>
- Command: `wmctrl -i -r <id> -e 0,x,y,w,h`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `wait_for_window`

- Category: windows
- Description: wait for window
- Parameters: `title`: <class 'str'>, `timeout`: <class 'float'>
- Command: `xdotool search --sync --onlyvisible --name <title>`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `set_clipboard`

- Category: clipboard
- Description: set clipboard
- Parameters: `text`: <class 'str'>
- Command: `xclip -selection clipboard -loops 0`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `get_clipboard`

- Category: clipboard
- Description: get clipboard
- Parameters: none
- Command: `xclip -selection clipboard -o`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `is_running`

- Category: processes
- Description: is running
- Parameters: `name`: <class 'str'>
- Command: `pgrep -x <name>`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `list_processes`

- Category: processes
- Description: list processes
- Parameters: none
- Command: `ps -eo pid,comm`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `close_app`

- Category: processes
- Description: close app
- Parameters: `pid`: <class 'int'>
- Command: `SIGTERM tracked pid`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `read_file`

- Category: files
- Description: read file
- Parameters: `path`: <class 'str'>
- Command: `pathlib.Path.read_text`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `write_file`

- Category: files
- Description: write file
- Parameters: `path`: <class 'str'>, `content`: <class 'str'>
- Command: `pathlib.Path.write_text`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `list_dir`

- Category: files
- Description: list dir
- Parameters: `path`: <class 'str'>
- Command: `pathlib.Path.iterdir`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `make_dir`

- Category: files
- Description: make dir
- Parameters: `path`: <class 'str'>
- Command: `pathlib.Path.mkdir`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## `delete_file`

- Category: files
- Description: delete file
- Parameters: `path`: <class 'str'>
- Command: `pathlib.Path.unlink/rmtree`
- Return/errors: structured result; validation errors are 422 and command failures are typed backend errors.
- Timeout: 10 seconds unless the operation has an explicit timeout parameter.
- Side effects/security: see registry validation; destructive actions are not undoable.
- Verification: Verified in container 2026-10-24 through `POST /operation` as desktop user `abc`.
The exact representative requests were `{"operation":"list_windows"}`, `{"operation":"open_terminal_in","path":"."}`,
`{"operation":"set_clipboard","text":"clipboard test"}`, and
`{"operation":"launch_browser_debug","url":"http://example.com"}`. The latter exposed
`curl http://127.0.0.1:9222/json/version` inside the container. `wmctrl -lpG` listed terminal ID
`0x01800003`, and `xdotool getactivewindow getwindowname` reported the focused terminal.

## Tools and packages

The image installs `xdotool`, `scrot`, `wmctrl`, and `xclip`. Browser, terminal, file manager, and editor binaries are verified separately below.

## Discrepancies

`screen_size` is an authenticated API endpoint although the executor milestone described it as internal. `zoom` is host-only and therefore cannot be sent to `/operation` or `/action`.

## Known issues

`xdotool type` accepts non-ASCII input without returning an error in this image, but its rendered result was not machine-asserted. `set_clipboard` followed by `ctrl+v` is the recommended Unicode path because X11 clipboard content was read back exactly. `active_window` can fail when XFWM has no active client window.

## Adding an operation

Add one Pydantic model and `OperationDefinition` in `friday.operations.registry`, add argv and validation tests, run `python scripts/gen_operations_doc.py`, then commit the generated document.
