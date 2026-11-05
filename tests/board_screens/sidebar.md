# TASK-191 sidebar QA

Uses the existing Chromium harness with locally intercepted fixtures and strict CSP.
No external requests or dependencies were added. The existing board palette and
native navigation controls are reused.

| Flow | Result | Screenshot |
| --- | --- | --- |
| Desktop sidebar, all seven destinations | PASS | `sidebar/sidebar-1280.png` |
| Phone overlay, inert content, keyboard focus loop and Escape | PASS | `sidebar/sidebar-375.png` |
| 320px layout, source/timestamp separation, no horizontal overflow | PASS | Browser assertions |
| Saved desktop toggle, collapsed phone reload, disabled localStorage | PASS | Browser assertions |
| Direct tree/Kanban/notification links and focus | PASS | Browser assertions |
| Existing sticky header, routes, filters, print and keyboard flows | PASS | Existing regression matrix |
| Light/dark axe serious/critical checks, console and request errors | PASS; no errors | Browser assertions |

Visually inspected the desktop and phone screenshots. Fixed an overlapping phone
source/timestamp row found during inspection; the regression now checks their geometry.
`python3 tests/test_board_web.py` exited 0: runtime and Chromium tests executed.
Wheel installation test skipped because pip is missing.

`python3 tests/test_omi.py` exited 0 with final `ok`; includes the board runtime,
Chromium and accessibility checks. Wheel installation test skipped because pip is missing.

## Review round 1: Escape ownership

Repro: at desktop width, leave the sidebar open, focus the project search,
enter `TASK-115`, and press Escape. Before the fix, the sidebar closed, saved
`closed`, and moved focus to its toggle. The added browser assertion failed on
the original handler (`search Escape must leave sidebar open`).

The handler now closes only for focus inside navigation or on its toggle, or
for an open phone overlay. Browser checks cover unset and saved `open` preferences,
search clearing and retained focus, unrelated refresh-button focus, and closing
from both a sidebar link and the toggle. The existing toolbar zoom check explicitly
selects its collapsed-sidebar layout instead of depending on the search bug.

| Flow | Before | After | Evidence |
| --- | --- | --- | --- |
| Desktop search Escape preserves sidebar, preference and focus | FAIL | PASS | `escape-before/sidebar-search-escape-1280.png`, `escape-after/sidebar-search-escape-1280.png` |
| Desktop Escape on refresh leaves navigation and preference unchanged | Not run | PASS | Browser assertions |
| Escape from sidebar/toggle, phone overlay and focus restoration | Not rerun | PASS | Browser assertions at 1280/375/320px |

`python3 tests/test_board_web.py` exited 0 after the fix: runtime, Chromium,
light/dark axe, keyboard, print and layout checks executed; no browser console
or unexpected request errors. Wheel packaging skipped because pip is missing.

## Build round 3: phone preference isolation

Repro: clear `omi-board-sidebar`, load the project at 375px, and open the
sidebar. The original code stores `open`; closing the overlay can then store
`closed`, changing the desktop preference. The new browser regression fails
against the original implementation with `phone open preserves desktop preference`.

The shared persistence guard now saves only on desktop. Browser checks cover
unset, `open`, and `closed` preferences across phone opening and closing by
toggle, backdrop, Escape, and navigation link; phone reloads stay collapsed,
and desktop resize/reload restores the original preference. Existing desktop
keyboard persistence, Escape ownership, and disabled-storage checks remain.

| Flow | Before | After | Evidence |
| --- | --- | --- | --- |
| Phone opening preserves unset desktop preference | FAIL | PASS | `persistence-before/sidebar-375.png`, `persistence-after/sidebar-375.png`; storage assertions |
| All phone dismissal paths preserve each desktop preference | Not run | PASS | Browser assertions at 375px, resize/reload at 1280px |
| Open sidebar beside dashboard, cost tables and dependency graph | Not run | PASS | `scrollWidth <= innerWidth` assertions at 768px and 1024px |

The before/after phone screenshots were visually inspected: the overlay layout
is unchanged; the regression concerns stored state. The focused browser runs
reported no console or unexpected request errors. `python3 tests/test_board_web.py`
exited 0, executing runtime, Chromium, keyboard, light/dark axe, print, and layout
checks. Wheel packaging skipped because pip is missing.

`python3 tests/test_omi.py` also exited 0 with final `ok`, including the board
runtime and Chromium checks. Wheel packaging skipped because pip is missing.
