# Friday observations

## Capture contract

`GET /observation` takes one locked X11 snapshot containing a PNG screenshot, display size, filtered window list, active-window ID and class, and `focused_app`. The PNG is base64 only on the HTTP wire; the harness writes it to its trace directory and retains its path in state. `GET /active_window` performs the smaller fresh focus lookup used immediately before shortcut execution.

Observations deliberately never include clipboard contents, environment variables, file listings, or process listings.

## Window list rules

The server obtains windows with `wmctrl -lpGx` and the active ID with `xdotool getactivewindow`. Xdotool's decimal ID is converted once to canonical lower-case, eight-digit hexadecimal before it is compared with wmctrl output. The pure parser then:

- removes background windows whose class starts with `xfce4-panel` or `xfdesktop`;
- sanitizes untrusted titles by removing control characters, collapsing whitespace, and truncating them to 80 characters;
- marks the active window, puts it first, and caps the result at 15 windows;
- returns only `id`, `title`, `class_name`, and `active` for each window.

Window geometry, PID, and desktop number are intentionally omitted.

## Failure behaviour

| Failure | Behaviour |
| --- | --- |
| Screenshot/capture request fails | The injected harness observer retries once. A second failure records `status="failed"` and a final report; graph routing then goes to `finish`. |
| Window list, active ID, or class lookup fails | The screenshot and screen size are retained; `windows` is empty, focus is `other`, and `capture_error` is written to `observation.json`. |
| Invalid display geometry | The server returns its normal typed HTTP error. |

Each successful harness observation writes `screenshot.png` and `observation.json` (window metadata, focused app, timing, and any capture error) to the selected trace directory. Prompt text and image bytes are not placed in state or the JSON trace metadata.

## Focus lookup table

Matching is case-insensitive against both WM_CLASS components. Exact entries win; explicit prefixes are tried next; all remaining classes map to `other`.

| Observed WM_CLASS (`instance.class`) | `focused_app` |
| --- | --- |
| `chromium (/tmp/friday-chromium-debug).Chromium` | `browser` |
| `xfce4-terminal.Xfce4-terminal` | `terminal` |
| `thunar-real.Thunar-real` | `file_manager` |
| `org.xfce.mousepad.Org.xfce.mousepad` | `text_editor` |

These class strings were recorded from the Friday image using `wmctrl -lpGx` and `xprop -id <window-id> WM_CLASS` on 2026-10-25. The shared lookup implementation is `friday.actions.focus.focused_app_for`.
