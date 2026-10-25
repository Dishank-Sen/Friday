# Executor node

The executor node is the execution boundary of the harness loop. It runs the
action the guard allowed through the injected `Executor` exactly once and
records the outcome in `last_result`. Everything below is enforced by tests in
`tests/test_executor_node.py`, `tests/test_steps.py`, and the contract tests.

## Contract

- **Reads** `pending_action`, `guard_verdict`.
- **Writes** only `last_result`. It never writes `prompt`, `hint`, `history`,
  `pending_action`, `guard_verdict`, `status`, `step`, screenshot paths, or
  `final_report`, and it does not clear `pending_action` (decide overwrites it).
- The node module does no I/O itself: all desktop access goes through the
  injected `Executor` protocol (or `RemoteExecutor`). It does not import
  `friday.llm`, `docker`, `subprocess`, `requests`, `httpx`, `friday.sandbox`,
  or the desktop client directly — enforced by an import-boundary test. The
  exception classes in `friday.desktop.errors` are part of the boundary (the
  injected Executor raises them).

## Defensive checks

In order; each records a failed `last_result` and does nothing else:

1. `guard_verdict != "allow"` → error type `not_allowed` (defense in depth; the
   graph should never route here).
2. `pending_action` is `None`, or its kind is not an action (e.g. a system
   operation) → `internal_error`.
3. `pending_action["action"]` fails validation against the action union →
   `invalid_action`.

A guard-rejected action therefore never touches the executor, test-proven for
both the `allow` and `reject` paths.

## Error-type table

The layer's richer errors collapse into one small, fixed set:

| Layer error | last_result `error.type` | Notes |
| --- | --- | --- |
| `DesktopTimeoutError` | `timeout` | message: "outcome unknown: the action may have run; check the screen before repeating" |
| `DesktopConnectionError` | `connection` | message: "outcome unknown: the control server could not be reached" |
| `DesktopRequestError` < 500 | `rejected_by_server` | |
| `DesktopRequestError` >= 500 | `command_failed` | |
| any other `Exception` | `unknown` | short message, never a traceback |

Only `KeyboardInterrupt` and `SystemExit` propagate unchanged — they are never
caught. `bounds` and `not_available` are reserved in the fixed set but today map
to `rejected_by_server`/`command_failed` via the server's 4xx/5xx responses.

## last_result shape

A single-result shape that serializes to JSON:

```json
{
  "ok": false,
  "operation": "left_click",
  "detail": null,
  "error": {"type": "timeout", "message": "..."},
  "duration_ms": 12,
  "point": null,
  "image_path": null,
  "expected_result": null
}
```

- `ok` — whether the action succeeded.
- `operation` — the action name.
- `detail` — bounded to `ExecutorSettings.max_detail`; truncation is marked with
  a trailing `…`.
- `error` — `{type, message}` for failures, `null` on success.
- `duration_ms` — from the injected monotonic clock.
- `point` — the pixel point acted on, if the layer reported one.
- `image_path` — where an observation image was saved (via the trace writer);
  never the bytes themselves.
- `expected_result` — copied from `pending_action` for the verify step.

Image bytes are carried transiently and excluded from every serialization, so
state never contains image bytes. A future batch would **add** an `items` list
of the same records while the top-level fields keep describing the last item,
so existing readers (`facts`, `render`) do not break. `run_steps` is the single
execution path and today produces one item per call.

## Observation operations

Action-union observation operations (`screenshot`, `zoom`, `cursor_position`)
may return `image_png`. Those bytes are written through the trace writer's
`write_image` (sanitized name, step-indexed) and `last_result` holds only
`image_path`. Text results — for the observation-style *system operations*
(`list_windows`, `active_window`, `get_clipboard`, `read_file`) — are **not**
routed through this node: those are SystemOperations on a different endpoint and
are out of scope here. Read-type operations return untrusted text that will
reach the next prompt through `build_context`.

Secrets must not be typed through the model until a secrets layer exists. The
node never logs, traces, or stores typed text, clipboard contents, or file
contents; `detail` is suppressed for `type`, `key`, and `hold_key`. A canary
test asserts typed text never reaches `last_result`.

## What this node deliberately does not do

It does not wait for the screen, take a screenshot, retry, judge success, or
choose delays — `settle` and `verify` own those, and a real executor requires
real `settle` and `verify` in the composition root. It runs one action per step
(`max_steps_per_call = 1`); a longer sequence raises a clear
`ConfigurationError` ("batching is not enabled").

## Known gap: held input on an abnormal end

The server backend already calls `release_all()` on any action failure, so a
failed action releases held mouse buttons and keys. There is no host-side
`release_all` call, and a run that ends while input is held (for example a
`left_mouse_down` followed by a stop) is not released; the fix belongs to
`finish`/the runner later.

## Checkpoint re-execution risk

LangGraph replay after a checkpoint re-executes this node, so a checkpointed
and resumed run may apply the same action again. This is a known, documented
risk; guard against it with idempotent actions or a replay guard.