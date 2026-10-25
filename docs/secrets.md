# Secrets (task 6511, Layer 1)

This package holds the primitives that keep a secret value out of every place
it must never reach: repr, str, prompts, traces, logs, checkpoints, http error
bodies, and history.

It is deliberately pure. Nothing here does terminal I/O, touches the desktop,
or reaches the network — those live in the runner (terminal channel) and the
executor/typing path (Layer 2).

## SecretValue — the wrapper

A live secret is carried only inside a `SecretValue` handle. The handle is
hostile to accidental or deliberate extraction:

- `repr`, `str`, and f-string/`format` rendering all produce the constant
  marker `<secret>`, never the value.
- `json.dumps` raises `TypeError` (the value is not a serializable type).
- pydantic json-mode `model_dump` / `model_dump_json` raise
  `pydantic_core.PydanticSerializationError` when a field holds a `SecretValue`.
- pydantic python-mode `model_dump` returns the wrapper itself (its `repr` is
  redacted, so the dumped text never contains the value).
- `pickle.dumps` (and `__reduce__`) raise `TypeError` eagerly, so the value
  cannot be smuggled out of a session or a checkpoint snapshot.

The value itself lives in a private slot (`_val`) whose name is documented as
internal. The only function allowed to release it is
`friday.secrets.unwrap`, which refuses anything that is not a `SecretValue`.

```python
from friday.secrets import SecretValue, unwrap

secret = SecretValue("hunter2")
str(secret)      # "<secret>"
repr(secret)     # "<secret>"
unwrap(secret)   # "hunter2"  — the one typing gate
```

## SecretVault — name-only storage

The vault stores secrets by name and returns `SecretValue` handles. Nothing in
the vault logs, records, or inspects values. The protocol, plus an
in-process implementation:

- `SecretVault` — protocol: `names()`, `contains(name)`, `get(name)`,
  `store(name, secret)`, `drop(name)`.
- `MemorySecretVault` — in-process dict-backed vault for CLI/terminal secrets.

`names()` and `contains()` are what harness nodes use; they never see values.
The runner stores a secret exactly once via `store`, and the rest of the program
works only through `SecretValue` / `unwrap`.

## Redaction — the trust-boundary scrubber

- `redact(text, *secrets)` — replaces every occurrence of any secret value with
  the constant marker. Used on text that is about to cross a trust boundary
  (trace writes, log emission, http error bodies).
- `LoggingFilter(provider)` — a `logging.Filter` that redacts every active
  secret from each emitted record. `provider` is a zero-arg callable returning
  the current `SecretValue` set (e.g. a closure over a vault), so the filter
  always sees live secrets and never caches a stale value.

## Guarantees across the whole feature

For any `SecretValue`, the following hold with tests asserting them:

| Surface | Result |
| --- | --- |
| `repr` / `str` / f-string / `format` | constant `<secret>` |
| `json.dumps(secret)` | `TypeError` |
| `pickle.dumps(secret)` / `__reduce__` | `TypeError` (eager) |
| pydantic `model_dump_json` / `model_dump(mode="json")` | `PydanticSerializationError` |
| pydantic `model_dump()` (python mode) | returns the wrapper; no value in its text |
| `bytes(secret)` / `bool` conversion | `TypeError` |
| `logging` record (via `LoggingFilter`) | value replaced with `<secret>` |

Unwrapping is single-gated: only `unwrap()` returns the value, and only the one
typing function (Layer 2) may call it.

See `docs/harness.md` for the surrounding loop; this module is consumed by the
`ask_user` node, the CLI runner, and the executor typing path in later layers.

## Layer 2 — typing a secret (name-only, stdin, fresh-focus gate)

`type_secret` is an **action** (`TypeSecretAction` in `actions/models.py`) whose
only field is the secret *name*. The value never enters the action, state,
prompts, or any `last_result` detail. On execution:

1. `guard` parses it as a normal action (no approval requirement — it is the
   executor's focus gate and the vault that decide whether anything is typed).
2. `RemoteExecutor` intercepts it, resolves the name against an injected
   `SecretVault`, and calls `DesktopClient.type_secret(name, value)` only when
   the name is present. The value is unwrapped here — the one deliberate typing
   gate — and passed only to the dedicated endpoint.
3. `DesktopClient.type_secret` POSTs `{name, value}` to `/type_secret` only.
4. The server re-reads the focused window **fresh at execution time** and
   refuses to type unless the focused app is in a configured allowlist
   (default: `browser` only). On rejection nothing is typed and the 422 body
   carries only a generic message.
5. The value is streamed to `xdotool type --file -` as **stdin**, never as an
   argv element, so it is invisible even transiently in `ps`. It is written
   once, closed, and never logged.

**Error bodies never echo the value.** The server's global request-validation
handler strips `input`/`value`/`ctx` from every 422 detail (only `type`, `loc`,
`msg` survive), so a failed secret request — bad name, missing/unknown field,
focus rejection, or oversized value — returns a body that contains neither the
value nor the offending field. The `/operation` route similarly scrubs its
422 detail.

**The value still transits the HTTP body in Layer 2.** This is why the 422
scrub is load-bearing: the client holds the vault secret and must deliver it to
the typing backend over the control API. It is never persisted, never logged
(the uvicorn access log emits only the request line), and never echoed on
error. Keeping it out of the on-wire transport itself is out of scope for this
layer but is the known limitation noted here.

**Sensitivity in the harness.** `run_steps` treats `type_secret` like `type`/
`key`/`hold_key`: its result `detail` is never surfaced, so even a hypothetical
executor detail cannot leak the value into `last_result` or a future prompt.