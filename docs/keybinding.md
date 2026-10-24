# Friday keybindings

## Overview

`shortcut` is a named action: `{"action":"shortcut","name":"copy"}`. Logical names resolve against a fresh active-window lookup immediately before key injection, so the agent does not need to emit raw keys. `default` bindings apply to any focused app without an explicit binding; an explicit `n/a` does not fall back. Deprecated aliases remain accepted for compatibility.

## Binding matrix

| Name | Browser | Terminal | File manager | Text editor | Other | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `copy` | `ctrl+c` | `ctrl+shift+c` | `ctrl+c` | `ctrl+c` | `ctrl+c` | unverified |
| `cut` | `ctrl+x` | `n/a` | `ctrl+x` | `ctrl+x` | `ctrl+x` | unverified |
| `paste` | `ctrl+v` | `ctrl+shift+v` | `ctrl+v` | `ctrl+v` | `ctrl+v` | unverified |
| `select_all` | `ctrl+a` | `ctrl+shift+a` | `ctrl+a` | `ctrl+a` | `ctrl+a` | unverified |
| `undo` | `ctrl+z` | `n/a` | `ctrl+z` | `ctrl+z` | `ctrl+z` | unverified |
| `redo` | `ctrl+shift+z` | `n/a` | `ctrl+shift+z` | `ctrl+shift+z` | `ctrl+shift+z` | unverified |
| `save` | `ctrl+s` | `n/a` | `ctrl+s` | `ctrl+s` | `ctrl+s` | unverified |
| `find` | `ctrl+f` | `ctrl+shift+f` | `ctrl+f` | `ctrl+f` | `ctrl+f` | unverified |
| `text_line_start` | `Home` | `Home` | `Home` | `Home` | `Home` | unverified |
| `text_line_end` | `End` | `End` | `End` | `End` | `End` | unverified |
| `text_delete_word_back` | `ctrl+BackSpace` | `ctrl+BackSpace` | `ctrl+BackSpace` | `ctrl+BackSpace` | `ctrl+BackSpace` | unverified |
| `browser_focus_address_bar` | `ctrl+l` | `n/a` | `n/a` | `n/a` | `n/a` | unverified |
| `browser_new_tab` | `ctrl+t` | `n/a` | `n/a` | `n/a` | `n/a` | unverified |
| `browser_close_tab` | `ctrl+w` | `n/a` | `n/a` | `n/a` | `n/a` | unverified |
| `browser_next_tab` | `ctrl+Tab` | `n/a` | `n/a` | `n/a` | `n/a` | unverified |
| `browser_prev_tab` | `ctrl+shift+Tab` | `n/a` | `n/a` | `n/a` | `n/a` | unverified |
| `browser_reload` | `ctrl+r` | `n/a` | `n/a` | `n/a` | `n/a` | unverified |
| `browser_back` | `alt+Left` | `n/a` | `n/a` | `n/a` | `n/a` | unverified |
| `browser_forward` | `alt+Right` | `n/a` | `n/a` | `n/a` | `n/a` | unverified |
| `browser_zoom_in` | `ctrl+plus` | `n/a` | `n/a` | `n/a` | `n/a` | unverified |
| `browser_zoom_out` | `ctrl+minus` | `n/a` | `n/a` | `n/a` | `n/a` | unverified |
| `browser_zoom_reset` | `ctrl+0` | `n/a` | `n/a` | `n/a` | `n/a` | unverified |
| `browser_reopen_tab` | `ctrl+shift+t` | `n/a` | `n/a` | `n/a` | `n/a` | unverified |
| `form_next_field` | `Tab` | `Tab` | `Tab` | `Tab` | `Tab` | unverified |
| `form_prev_field` | `shift+Tab` | `shift+Tab` | `shift+Tab` | `shift+Tab` | `shift+Tab` | unverified |
| `form_submit` | `Return` | `Return` | `Return` | `Return` | `Return` | unverified |
| `form_cancel` | `Escape` | `Escape` | `Escape` | `Escape` | `Escape` | unverified |
| `form_toggle` | `space` | `space` | `space` | `space` | `space` | unverified |
| `form_option_up` | `Up` | `Up` | `Up` | `Up` | `Up` | unverified |
| `form_option_down` | `Down` | `Down` | `Down` | `Down` | `Down` | unverified |
| `window_switch` | `alt+Tab` | `alt+Tab` | `alt+Tab` | `alt+Tab` | `alt+Tab` | unverified |
| `window_close` | `alt+F4` | `alt+F4` | `alt+F4` | `alt+F4` | `alt+F4` | unverified |
| `window_maximize` | `alt+F10` | `alt+F10` | `alt+F10` | `alt+F10` | `alt+F10` | unverified |
| `window_minimize` | `alt+F9` | `alt+F9` | `alt+F9` | `alt+F9` | `alt+F9` | unverified |
| `window_show_desktop` | `ctrl+alt+d` | `ctrl+alt+d` | `ctrl+alt+d` | `ctrl+alt+d` | `ctrl+alt+d` | unverified |
| `terminal_interrupt` | `n/a` | `ctrl+c` | `n/a` | `n/a` | `n/a` | unverified |
| `terminal_eof` | `n/a` | `ctrl+d` | `n/a` | `n/a` | `n/a` | unverified |
| `terminal_clear` | `n/a` | `ctrl+l` | `n/a` | `n/a` | `n/a` | unverified |
| `terminal_history_prev` | `n/a` | `Up` | `n/a` | `n/a` | `n/a` | unverified |
| `file_rename` | `n/a` | `n/a` | `F2` | `n/a` | `n/a` | unverified |
| `file_new_folder` | `n/a` | `n/a` | `ctrl+shift+n` | `n/a` | `n/a` | unverified |
| `file_go_to_path` | `n/a` | `n/a` | `ctrl+l` | `n/a` | `n/a` | unverified |
| `file_delete_to_trash` | `n/a` | `n/a` | `Delete` | `n/a` | `n/a` | unverified |
| `file_up` | `n/a` | `n/a` | `alt+Up` | `n/a` | `n/a` | unverified |
## Text

### `copy`

- Description: Copy selection.
- Bindings: browser: ctrl+c, terminal: ctrl+shift+c, file_manager: ctrl+c, text_editor: ctrl+c, other: ctrl+c
- Expected effect: Clipboard receives selection.
- Caveats: ctrl+c interrupts a terminal program.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `cut`

- Description: Cut selection.
- Bindings: browser: ctrl+x, terminal: n/a, file_manager: ctrl+x, text_editor: ctrl+x, other: ctrl+x
- Expected effect: Selection is removed to clipboard.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `paste`

- Description: Paste clipboard.
- Bindings: browser: ctrl+v, terminal: ctrl+shift+v, file_manager: ctrl+v, text_editor: ctrl+v, other: ctrl+v
- Expected effect: Clipboard text is inserted.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `select_all`

- Description: Select all.
- Bindings: browser: ctrl+a, terminal: ctrl+shift+a, file_manager: ctrl+a, text_editor: ctrl+a, other: ctrl+a
- Expected effect: All selectable content is selected.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `undo`

- Description: Undo edit.
- Bindings: browser: ctrl+z, terminal: n/a, file_manager: ctrl+z, text_editor: ctrl+z, other: ctrl+z
- Expected effect: Most recent edit is reversed.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `redo`

- Description: Redo edit.
- Bindings: browser: ctrl+shift+z, terminal: n/a, file_manager: ctrl+shift+z, text_editor: ctrl+shift+z, other: ctrl+shift+z
- Expected effect: Undone edit is restored.
- Caveats: Some apps use ctrl+y.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `save`

- Description: Save document.
- Bindings: browser: ctrl+s, terminal: n/a, file_manager: ctrl+s, text_editor: ctrl+s, other: ctrl+s
- Expected effect: Document is saved.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `find`

- Description: Open find UI.
- Bindings: browser: ctrl+f, terminal: ctrl+shift+f, file_manager: ctrl+f, text_editor: ctrl+f, other: ctrl+f
- Expected effect: Find UI appears.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `text_line_start`

- Description: Move to line start.
- Bindings: browser: Home, terminal: Home, file_manager: Home, text_editor: Home, other: Home
- Expected effect: Caret moves to line start.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `text_line_end`

- Description: Move to line end.
- Bindings: browser: End, terminal: End, file_manager: End, text_editor: End, other: End
- Expected effect: Caret moves to line end.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `text_delete_word_back`

- Description: Delete previous word.
- Bindings: browser: ctrl+BackSpace, terminal: ctrl+BackSpace, file_manager: ctrl+BackSpace, text_editor: ctrl+BackSpace, other: ctrl+BackSpace
- Expected effect: Word before caret is removed.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

## Browser

### `browser_focus_address_bar`

- Description: Focus address bar.
- Bindings: browser: ctrl+l, terminal: n/a, file_manager: n/a, text_editor: n/a, other: n/a
- Expected effect: Address bar is focused.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `browser_new_tab`

- Description: Open tab.
- Bindings: browser: ctrl+t, terminal: n/a, file_manager: n/a, text_editor: n/a, other: n/a
- Expected effect: New tab appears.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `browser_close_tab`

- Description: Close tab.
- Bindings: browser: ctrl+w, terminal: n/a, file_manager: n/a, text_editor: n/a, other: n/a
- Expected effect: Focused tab closes.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `browser_next_tab`

- Description: Focus next tab.
- Bindings: browser: ctrl+Tab, terminal: n/a, file_manager: n/a, text_editor: n/a, other: n/a
- Expected effect: Next tab is focused.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `browser_prev_tab`

- Description: Focus previous tab.
- Bindings: browser: ctrl+shift+Tab, terminal: n/a, file_manager: n/a, text_editor: n/a, other: n/a
- Expected effect: Previous tab is focused.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `browser_reload`

- Description: Reload page.
- Bindings: browser: ctrl+r, terminal: n/a, file_manager: n/a, text_editor: n/a, other: n/a
- Expected effect: Focused tab reloads.
- Caveats: F5 also reloads Chromium.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `browser_back`

- Description: Navigate back.
- Bindings: browser: alt+Left, terminal: n/a, file_manager: n/a, text_editor: n/a, other: n/a
- Expected effect: Previous history entry appears.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `browser_forward`

- Description: Navigate forward.
- Bindings: browser: alt+Right, terminal: n/a, file_manager: n/a, text_editor: n/a, other: n/a
- Expected effect: Next history entry appears.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `browser_zoom_in`

- Description: Increase zoom.
- Bindings: browser: ctrl+plus, terminal: n/a, file_manager: n/a, text_editor: n/a, other: n/a
- Expected effect: Page zoom increases.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `browser_zoom_out`

- Description: Decrease zoom.
- Bindings: browser: ctrl+minus, terminal: n/a, file_manager: n/a, text_editor: n/a, other: n/a
- Expected effect: Page zoom decreases.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `browser_zoom_reset`

- Description: Reset zoom.
- Bindings: browser: ctrl+0, terminal: n/a, file_manager: n/a, text_editor: n/a, other: n/a
- Expected effect: Page zoom returns to 100%.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `browser_reopen_tab`

- Description: Reopen closed tab.
- Bindings: browser: ctrl+shift+t, terminal: n/a, file_manager: n/a, text_editor: n/a, other: n/a
- Expected effect: Last closed tab reopens.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

## Form

### `form_next_field`

- Description: Focus next field.
- Bindings: browser: Tab, terminal: Tab, file_manager: Tab, text_editor: Tab, other: Tab
- Expected effect: Focus advances.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `form_prev_field`

- Description: Focus previous field.
- Bindings: browser: shift+Tab, terminal: shift+Tab, file_manager: shift+Tab, text_editor: shift+Tab, other: shift+Tab
- Expected effect: Focus moves backward.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `form_submit`

- Description: Submit form.
- Bindings: browser: Return, terminal: Return, file_manager: Return, text_editor: Return, other: Return
- Expected effect: Form submits when supported.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `form_cancel`

- Description: Cancel focused UI.
- Bindings: browser: Escape, terminal: Escape, file_manager: Escape, text_editor: Escape, other: Escape
- Expected effect: Dialog or popup closes when supported.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `form_toggle`

- Description: Toggle control.
- Bindings: browser: space, terminal: space, file_manager: space, text_editor: space, other: space
- Expected effect: Focused control toggles.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `form_option_up`

- Description: Move option up.
- Bindings: browser: Up, terminal: Up, file_manager: Up, text_editor: Up, other: Up
- Expected effect: Previous option is selected.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `form_option_down`

- Description: Move option down.
- Bindings: browser: Down, terminal: Down, file_manager: Down, text_editor: Down, other: Down
- Expected effect: Next option is selected.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

## Window

### `window_switch`

- Description: Switch window.
- Bindings: browser: alt+Tab, terminal: alt+Tab, file_manager: alt+Tab, text_editor: alt+Tab, other: alt+Tab
- Expected effect: Window switcher changes focus.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `window_close`

- Description: Close window.
- Bindings: browser: alt+F4, terminal: alt+F4, file_manager: alt+F4, text_editor: alt+F4, other: alt+F4
- Expected effect: Focused window closes.
- Caveats: None.
- Risk flag: risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `window_maximize`

- Description: Toggle maximize.
- Bindings: browser: alt+F10, terminal: alt+F10, file_manager: alt+F10, text_editor: alt+F10, other: alt+F10
- Expected effect: Focused window maximizes or restores.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `window_minimize`

- Description: Minimize window.
- Bindings: browser: alt+F9, terminal: alt+F9, file_manager: alt+F9, text_editor: alt+F9, other: alt+F9
- Expected effect: Focused window minimizes.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `window_show_desktop`

- Description: Show desktop.
- Bindings: browser: ctrl+alt+d, terminal: ctrl+alt+d, file_manager: ctrl+alt+d, text_editor: ctrl+alt+d, other: ctrl+alt+d
- Expected effect: Windows hide to reveal desktop.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

## Terminal

### `terminal_interrupt`

- Description: Interrupt foreground command.
- Bindings: browser: n/a, terminal: ctrl+c, file_manager: n/a, text_editor: n/a, other: n/a
- Expected effect: Foreground command receives SIGINT.
- Caveats: None.
- Risk flag: risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `terminal_eof`

- Description: Send EOF.
- Bindings: browser: n/a, terminal: ctrl+d, file_manager: n/a, text_editor: n/a, other: n/a
- Expected effect: Shell exits or input receives EOF.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `terminal_clear`

- Description: Clear terminal.
- Bindings: browser: n/a, terminal: ctrl+l, file_manager: n/a, text_editor: n/a, other: n/a
- Expected effect: Terminal viewport clears.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `terminal_history_prev`

- Description: Previous history entry.
- Bindings: browser: n/a, terminal: Up, file_manager: n/a, text_editor: n/a, other: n/a
- Expected effect: Previous command appears.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

## File Manager

### `file_rename`

- Description: Rename selected file.
- Bindings: browser: n/a, terminal: n/a, file_manager: F2, text_editor: n/a, other: n/a
- Expected effect: Rename editor opens.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `file_new_folder`

- Description: Create folder.
- Bindings: browser: n/a, terminal: n/a, file_manager: ctrl+shift+n, text_editor: n/a, other: n/a
- Expected effect: New-folder dialog opens.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `file_go_to_path`

- Description: Focus location entry.
- Bindings: browser: n/a, terminal: n/a, file_manager: ctrl+l, text_editor: n/a, other: n/a
- Expected effect: Location entry is focused.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `file_delete_to_trash`

- Description: Move selection to trash.
- Bindings: browser: n/a, terminal: n/a, file_manager: Delete, text_editor: n/a, other: n/a
- Expected effect: Selection moves to trash.
- Caveats: None.
- Risk flag: risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

### `file_up`

- Description: Open parent folder.
- Bindings: browser: n/a, terminal: n/a, file_manager: alt+Up, text_editor: n/a, other: n/a
- Expected effect: Parent directory appears.
- Caveats: None.
- Risk flag: not risky
- Status: unverified
- Verification evidence: Unverified pending container verification.

## Deprecated aliases

| Alias | Logical name |
| --- | --- |
| `text_copy` | `copy` |
| `terminal_copy` | `copy` |
| `text_cut` | `cut` |
| `text_paste` | `paste` |
| `terminal_paste` | `paste` |
| `text_select_all` | `select_all` |
| `text_undo` | `undo` |
| `text_redo` | `redo` |
| `text_save` | `save` |
| `browser_find` | `find` |

## Same keys, different contexts

| Keys | Meaning |
| --- | --- |
| `ctrl+c` | `copy` normally copies; `terminal_interrupt` sends SIGINT. |
| `ctrl+l` | Browser address bar, terminal clear, and file-manager location entry. |
| `ctrl+shift+c` | `copy` in a terminal. |

## Gaps

No custom XFCE keybindings are created. Unavailable shortcuts return a helpful failure; use direct operations from `docs/operations.md` until a later container-init task adds a custom binding.

## Known issues

The browser viewer can swallow shortcuts pressed manually in the host browser; xdotool injection into X11 is unaffected. Entries marked unverified need an objective or visual check in the current image.

## Adding a shortcut

Add one logical registry entry with bindings, test all focused-app resolutions, run `python scripts/gen_keybinding_doc.py`, and commit this generated document.
