# Verify node

The verify node reconciles what just happened against the screen and advances
the loop. It is the **single owner** of `step`, `history`, and `stuck_count` —
no other node writes them. It never calls a model and never interprets the
free-text `expected_result`; the next `decide` call judges `expected_result`
using the fresh screenshot that `settle` captured.

## Contract

- **Reads:** `pending_action`, `last_result`, `screenshot_path`,
  `prev_screenshot_path`, `focused_app`, `step`, `history`, `stuck_count`,
  `decision`, `hint`.
- **Writes ONLY:** `step`, `history`, `stuck_count`, `hint`. It never writes
  `prompt`, `pending_action`, `last_result`, `guard_verdict`, `decision`,
  `status`, `final_report`, or screenshot paths.
- Never raises for an expected problem (missing/unreadable screenshot, probe
  errors, size mismatch). Routing stays the fixed edge `verify -> build_context`.
- Injected dependencies are a frozen `VerifyDeps` dataclass and
  `make_verify(deps)`, like the other nodes: `load_screenshot` (reuses
  decide's loader), an optional `BrowserProbe`, and `settings`.

## Step outcome

A pure function in `friday.harness.verify_diff` labels the step:

| Outcome | Meaning |
| --- | --- |
| `failed` | `last_result.ok` is False. |
| `no_visible_change` | the operation is expected to change the screen but the diff is small/`unchanged`. |
| `changed` | the operation changed the screen (ratio at/above `min_changed_ratio`, or size changed). |
| `no_change_expected` | the operation is not expected to change the screen and it did not. |
| `unknown` | screenshots unusable (missing, unreadable, or paths absent). |

`EXPECTS_SCREEN_CHANGE` keys an operation's screen-change expectation
(clicks, `type`, `key`, `shortcut`, `open_url`, `launch_app`, `scroll`, drag,
`focus_window`: **True**; `wait`, `mouse_move`, `hold_key`, observation and
read-only operations: **False**). The defaults are a starting point and are
documented in `verify_settings`.

## Bookkeeping

- `step` increments for every executed action (a step is an executed action;
  rejects and invalid replies do not count).
- `stuck_count`: +1 on `failed` or `no_visible_change`, reset to 0 on
  `changed`, unchanged on `no_change_expected` and `unknown`.
- `history`: one record per step, matching the shape guard and `facts`
  consume — it keeps `decision`, `action` (the sanitized pending payload) and
  `outcome`, and adds `operation`, `ok`, `error` (if any), `expected_result`
  (copied unchanged, bounded), `changed_ratio` (rounded), and a `browser`
  sub-record when a probe is available. The list is bounded to
  `DiffSettings.max_history` entries (oldest dropped), so the existing
  `facts`/render bounds stay the single mechanism.
- `hint`: a fixed message on `no_visible_change` ("Your last action had no
  visible effect on the screen. Try a different approach.") and a stronger one
  when `stuck_count` crosses the configured warning level. Messages never
  include page text, titles, URLs or model text. A non-empty existing `hint`
  is never overwritten.

## History record shape

```json
{
  "decision": "action",
  "outcome": "no_visible_change",
  "action": {"action": "open_url", "url": "https://github.com"},
  "operation": "open_url",
  "ok": true,
  "expected_result": "the github profile loads",
  "changed_ratio": 0.0001,
  "browser": {"url": "https://github.com", "title": "GitHub", "ready_state": "complete", "loading": false, "tab_count": 2}
}
```

The `action` field keeps the exact discriminator shape the guard's repeat check
and `facts._history_entry` read, so the record stays compatible with both.
Sensitive input (`type`/`key`/`hold_key`) is recorded by kind and length, never
the typed text.

## What verify deliberately does not do

It does not judge `expected_result`, call a model, or drive the browser. Read
text (`read_file`, `get_clipboard`) and browser facts are recorded only as
data; the next `decide` decides. `expected_result` is copied untouched into the
history record — verify never interprets it.