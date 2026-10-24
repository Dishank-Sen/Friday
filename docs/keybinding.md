# Friday keybindings

## Overview

`shortcut` is a named Friday action: `{"action":"shortcut","name":"browser_focus_address_bar"}`. Names map to validated xdotool key syntax in the registry, so an agent does not need to emit raw key strings for common operations. Keystrokes are delivered to the currently focused X11 window; every entry therefore states its required focus.

## Summary

| Name | Keys | Context | Requires focus | Status |
| --- | --- | --- | --- | --- |
| `text_select_all` | `ctrl+a` | text | `any` | unverified |
| `text_copy` | `ctrl+c` | text | `any` | unverified |
| `text_cut` | `ctrl+x` | text | `any` | unverified |
| `text_paste` | `ctrl+v` | text | `any` | unverified |
| `text_undo` | `ctrl+z` | text | `any` | unverified |
| `text_redo` | `ctrl+shift+z` | text | `any` | unverified |
| `text_save` | `ctrl+s` | text | `mousepad` | unverified |
| `text_line_start` | `Home` | text | `any` | unverified |
| `text_line_end` | `End` | text | `any` | unverified |
| `text_delete_word_back` | `ctrl+BackSpace` | text | `any` | unverified |
| `browser_focus_address_bar` | `ctrl+l` | browser | `chromium` | unverified |
| `browser_new_tab` | `ctrl+t` | browser | `chromium` | unverified |
| `browser_close_tab` | `ctrl+w` | browser | `chromium` | unverified |
| `browser_next_tab` | `ctrl+Tab` | browser | `chromium` | unverified |
| `browser_prev_tab` | `ctrl+shift+Tab` | browser | `chromium` | unverified |
| `browser_reload` | `ctrl+r` | browser | `chromium` | unverified |
| `browser_back` | `alt+Left` | browser | `chromium` | unverified |
| `browser_forward` | `alt+Right` | browser | `chromium` | unverified |
| `browser_find` | `ctrl+f` | browser | `chromium` | unverified |
| `browser_zoom_in` | `ctrl+plus` | browser | `chromium` | unverified |
| `browser_zoom_out` | `ctrl+minus` | browser | `chromium` | unverified |
| `browser_zoom_reset` | `ctrl+0` | browser | `chromium` | unverified |
| `browser_reopen_tab` | `ctrl+shift+t` | browser | `chromium` | unverified |
| `form_next_field` | `Tab` | form | `any` | unverified |
| `form_prev_field` | `shift+Tab` | form | `any` | unverified |
| `form_submit` | `Return` | form | `any` | unverified |
| `form_cancel` | `Escape` | form | `any` | unverified |
| `form_toggle` | `space` | form | `any` | unverified |
| `form_option_up` | `Up` | form | `any` | unverified |
| `form_option_down` | `Down` | form | `any` | unverified |
| `window_switch` | `alt+Tab` | window | `any` | unverified |
| `window_close` | `alt+F4` | window | `any` | unverified |
| `window_maximize` | `alt+F10` | window | `any` | unverified |
| `window_minimize` | `alt+F9` | window | `any` | unverified |
| `window_show_desktop` | `ctrl+alt+d` | window | `any` | unverified |
| `terminal_interrupt` | `ctrl+c` | terminal | `xfce4-terminal` | unverified |
| `terminal_eof` | `ctrl+d` | terminal | `xfce4-terminal` | unverified |
| `terminal_clear` | `ctrl+l` | terminal | `xfce4-terminal` | unverified |
| `terminal_history_prev` | `Up` | terminal | `xfce4-terminal` | unverified |
| `terminal_copy` | `ctrl+shift+c` | terminal | `xfce4-terminal` | unverified |
| `terminal_paste` | `ctrl+shift+v` | terminal | `xfce4-terminal` | unverified |
| `file_rename` | `F2` | file_manager | `thunar` | unverified |
| `file_new_folder` | `ctrl+shift+n` | file_manager | `thunar` | unverified |
| `file_go_to_path` | `ctrl+l` | file_manager | `thunar` | unverified |
| `file_delete_to_trash` | `Delete` | file_manager | `thunar` | unverified |
| `file_up` | `alt+Up` | file_manager | `thunar` | unverified |
## Text

### `text_select_all`

- Description: Select all text.
- Keys: `ctrl+a`
- Requires focus: `any`
- Expected effect: All text is selected.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/text/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `text_copy`

- Description: Copy selection.
- Keys: `ctrl+c`
- Requires focus: `any`
- Expected effect: Clipboard receives selection.
- Caveats: Use terminal_copy in terminals.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/text/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `text_cut`

- Description: Cut selection.
- Keys: `ctrl+x`
- Requires focus: `any`
- Expected effect: Selection is removed to clipboard.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/text/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `text_paste`

- Description: Paste clipboard.
- Keys: `ctrl+v`
- Requires focus: `any`
- Expected effect: Clipboard text is inserted.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/text/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `text_undo`

- Description: Undo edit.
- Keys: `ctrl+z`
- Requires focus: `any`
- Expected effect: Most recent edit is reversed.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/text/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `text_redo`

- Description: Redo edit.
- Keys: `ctrl+shift+z`
- Requires focus: `any`
- Expected effect: Undone edit is restored.
- Caveats: Some apps use ctrl+y instead.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/text/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `text_save`

- Description: Save document.
- Keys: `ctrl+s`
- Requires focus: `mousepad`
- Expected effect: Document is saved.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/text/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `text_line_start`

- Description: Move to line start.
- Keys: `Home`
- Requires focus: `any`
- Expected effect: Caret moves to line start.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/text/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `text_line_end`

- Description: Move to line end.
- Keys: `End`
- Requires focus: `any`
- Expected effect: Caret moves to line end.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/text/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `text_delete_word_back`

- Description: Delete previous word.
- Keys: `ctrl+BackSpace`
- Requires focus: `any`
- Expected effect: Word before caret is removed.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/text/after.png`. Visual/objective per-shortcut effect still needs confirmation.

## Browser

### `browser_focus_address_bar`

- Description: Focus address bar.
- Keys: `ctrl+l`
- Requires focus: `chromium`
- Expected effect: Address bar is focused.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/browser/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `browser_new_tab`

- Description: Open tab.
- Keys: `ctrl+t`
- Requires focus: `chromium`
- Expected effect: New tab appears.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/browser/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `browser_close_tab`

- Description: Close tab.
- Keys: `ctrl+w`
- Requires focus: `chromium`
- Expected effect: Focused tab closes.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/browser/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `browser_next_tab`

- Description: Next tab.
- Keys: `ctrl+Tab`
- Requires focus: `chromium`
- Expected effect: Next tab is focused.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/browser/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `browser_prev_tab`

- Description: Previous tab.
- Keys: `ctrl+shift+Tab`
- Requires focus: `chromium`
- Expected effect: Previous tab is focused.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/browser/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `browser_reload`

- Description: Reload page.
- Keys: `ctrl+r`
- Requires focus: `chromium`
- Expected effect: Focused tab reloads.
- Caveats: F5 is also supported by Chromium.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/browser/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `browser_back`

- Description: Navigate back.
- Keys: `alt+Left`
- Requires focus: `chromium`
- Expected effect: Previous history entry appears.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/browser/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `browser_forward`

- Description: Navigate forward.
- Keys: `alt+Right`
- Requires focus: `chromium`
- Expected effect: Next history entry appears.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/browser/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `browser_find`

- Description: Open find bar.
- Keys: `ctrl+f`
- Requires focus: `chromium`
- Expected effect: Find bar appears.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/browser/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `browser_zoom_in`

- Description: Increase zoom.
- Keys: `ctrl+plus`
- Requires focus: `chromium`
- Expected effect: Page zoom increases.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/browser/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `browser_zoom_out`

- Description: Decrease zoom.
- Keys: `ctrl+minus`
- Requires focus: `chromium`
- Expected effect: Page zoom decreases.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/browser/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `browser_zoom_reset`

- Description: Reset zoom.
- Keys: `ctrl+0`
- Requires focus: `chromium`
- Expected effect: Page zoom returns to 100%.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/browser/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `browser_reopen_tab`

- Description: Reopen closed tab.
- Keys: `ctrl+shift+t`
- Requires focus: `chromium`
- Expected effect: Most recently closed tab reopens.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/browser/after.png`. Visual/objective per-shortcut effect still needs confirmation.

## Form

### `form_next_field`

- Description: Focus next field.
- Keys: `Tab`
- Requires focus: `any`
- Expected effect: Focus advances.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/form/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `form_prev_field`

- Description: Focus previous field.
- Keys: `shift+Tab`
- Requires focus: `any`
- Expected effect: Focus moves backward.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/form/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `form_submit`

- Description: Submit focused form.
- Keys: `Return`
- Requires focus: `any`
- Expected effect: Form submits when supported.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/form/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `form_cancel`

- Description: Cancel focused UI.
- Keys: `Escape`
- Requires focus: `any`
- Expected effect: Dialog or popup closes when supported.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/form/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `form_toggle`

- Description: Toggle focused control.
- Keys: `space`
- Requires focus: `any`
- Expected effect: Checkbox or button toggles.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/form/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `form_option_up`

- Description: Move option up.
- Keys: `Up`
- Requires focus: `any`
- Expected effect: Previous option is selected.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/form/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `form_option_down`

- Description: Move option down.
- Keys: `Down`
- Requires focus: `any`
- Expected effect: Next option is selected.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/form/after.png`. Visual/objective per-shortcut effect still needs confirmation.

## Window

### `window_switch`

- Description: Switch window.
- Keys: `alt+Tab`
- Requires focus: `any`
- Expected effect: Window switcher changes focus.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/window/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `window_close`

- Description: Close focused window.
- Keys: `alt+F4`
- Requires focus: `any`
- Expected effect: Focused window closes.
- Caveats: None.
- Risk flag: risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/window/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `window_maximize`

- Description: Toggle maximize.
- Keys: `alt+F10`
- Requires focus: `any`
- Expected effect: Focused window maximizes or restores.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/window/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `window_minimize`

- Description: Minimize focused window.
- Keys: `alt+F9`
- Requires focus: `any`
- Expected effect: Focused window minimizes.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/window/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `window_show_desktop`

- Description: Show desktop.
- Keys: `ctrl+alt+d`
- Requires focus: `any`
- Expected effect: Windows hide to reveal desktop.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/window/after.png`. Visual/objective per-shortcut effect still needs confirmation.

## Terminal

### `terminal_interrupt`

- Description: Interrupt foreground command.
- Keys: `ctrl+c`
- Requires focus: `xfce4-terminal`
- Expected effect: Foreground command receives SIGINT.
- Caveats: Use text_copy in GUI text fields.
- Risk flag: risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/terminal/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `terminal_eof`

- Description: Send EOF.
- Keys: `ctrl+d`
- Requires focus: `xfce4-terminal`
- Expected effect: Shell exits or input receives EOF.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/terminal/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `terminal_clear`

- Description: Clear terminal.
- Keys: `ctrl+l`
- Requires focus: `xfce4-terminal`
- Expected effect: Terminal viewport clears.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/terminal/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `terminal_history_prev`

- Description: Previous history entry.
- Keys: `Up`
- Requires focus: `xfce4-terminal`
- Expected effect: Previous command appears.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/terminal/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `terminal_copy`

- Description: Copy terminal selection.
- Keys: `ctrl+shift+c`
- Requires focus: `xfce4-terminal`
- Expected effect: Clipboard receives selection.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/terminal/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `terminal_paste`

- Description: Paste into terminal.
- Keys: `ctrl+shift+v`
- Requires focus: `xfce4-terminal`
- Expected effect: Clipboard text is pasted.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/terminal/after.png`. Visual/objective per-shortcut effect still needs confirmation.

## File Manager

### `file_rename`

- Description: Rename selected file.
- Keys: `F2`
- Requires focus: `thunar`
- Expected effect: Rename editor opens.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/file_manager/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `file_new_folder`

- Description: Create folder.
- Keys: `ctrl+shift+n`
- Requires focus: `thunar`
- Expected effect: New-folder dialog opens.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/file_manager/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `file_go_to_path`

- Description: Focus location entry.
- Keys: `ctrl+l`
- Requires focus: `thunar`
- Expected effect: Location entry is focused.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/file_manager/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `file_delete_to_trash`

- Description: Move selection to trash.
- Keys: `Delete`
- Requires focus: `thunar`
- Expected effect: Selected files move to trash.
- Caveats: None.
- Risk flag: risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/file_manager/after.png`. Visual/objective per-shortcut effect still needs confirmation.

### `file_up`

- Description: Open parent folder.
- Keys: `alt+Up`
- Requires focus: `thunar`
- Expected effect: Parent directory appears.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Executed 2026-10-24 with `POST /action` and returned HTTP 200; visual evidence: `docs/assets/keybindings/file_manager/after.png`. Visual/objective per-shortcut effect still needs confirmation.

## Same keys, different contexts

| Keys | Context-dependent meaning |
| --- | --- |
| `ctrl+c` | `text_copy` copies GUI text; `terminal_interrupt` sends SIGINT. |
| `ctrl+l` | Browser address bar, terminal clear, and Thunar location entry. |
| `ctrl+shift+c` | Terminal copy; use `text_copy` for ordinary GUI text. |

## Gaps

No custom XFCE keybindings were created. Operations without a reliable default binding should use the direct commands in `docs/operations.md`; a later container-init script may define custom bindings if needed.

## Known issues

The browser viewer can consume browser and common editing shortcuts when pressed manually in the host browser. That does not affect `xdotool`, which injects into X11. This xdotool version has no `getwindowclassname` or `getwindowclass` command; `xprop WM_CLASS` and `wmctrl -lx` were used instead. `window_show_desktop` may expose XFCE's application finder rather than only hiding windows.

## Adding a shortcut

Add one `ShortcutDefinition` in `friday.shortcuts.registry`, ensure all key strings normalize through `keys.py`, add tests, run `python scripts/gen_keybinding_doc.py`, and commit the generated document.
