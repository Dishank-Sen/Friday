| Node | Reads | Writes |
| --- | --- | --- |
| observe | — | final_report, focused_app, screen_size, screenshot_path, status, windows |
| build_context | focused_app, goal, guard_verdict, hint, history, last_result, max_steps, pending_action, retries, screen_size, screenshot_path, step, windows | hint, prompt |
| decide | prompt, screenshot_path | decision, hint, pending_action, retries |
| guard | focused_app, history, max_steps, pending_action, retries, screen_size, started_at, status, step, stuck_count | guard_verdict, hint |
| executor | guard_verdict, pending_action | last_result |
| settle | screenshot_path | focused_app, prev_screenshot_path, screen_size, screenshot_path, windows |
| verify | decision, hint, history, last_result, pending_action, prev_screenshot_path, screenshot_path, step, stuck_count | hint, history, step, stuck_count |
| finish | decision, final_report, guard_verdict, hint, status | final_report, status |