# TASK-192 header scroll evidence

Root cause: the unscoped `.top{position:static}` rule in the TASK-127 inbox styles overrode the shared sticky header. Removed that rule; the print-only static rule remains.

Regression: Chromium scrolls each route to 300px and the document bottom at 375×800 and 1280×800. Short fixtures receive 80 paragraphs inside main to guarantee scrollable content. All 24 checks failed before the CSS fix (header top < 0), then passed (top = 0).

Screenshots show the 300px scroll position. Each directory contains `header-<page>-375.png` and `header-<page>-1280.png`.

| Flow | Before | After | Screenshot names |
| --- | --- | --- | --- |
| projects | FAIL | PASS | `header-before/header-projects-{375,1280}.png`, `header-after/header-projects-{375,1280}.png` |
| dashboard | FAIL | PASS | `header-before/header-dashboard-{375,1280}.png`, `header-after/header-dashboard-{375,1280}.png` |
| task | FAIL | PASS | `header-before/header-task-{375,1280}.png`, `header-after/header-task-{375,1280}.png` |
| inbox | FAIL | PASS | `header-before/header-inbox-{375,1280}.png`, `header-after/header-inbox-{375,1280}.png` |
| cost | FAIL | PASS | `header-before/header-cost-{375,1280}.png`, `header-after/header-cost-{375,1280}.png` |
| graph | FAIL | PASS | `header-before/header-graph-{375,1280}.png`, `header-after/header-graph-{375,1280}.png` |

The existing Playwright harness intercepts all requests locally, rejects unexpected/non-GET requests, and checks browser page errors and console errors. The passing browser suite reported none. Desktop and mobile dashboard screenshots were also visually inspected.

`python3 tests/test_board_web.py`: exit 0; browser, runtime, accessibility and print tests ran. Wheel packaging skipped because pip is missing.

`python3 tests/test_omi.py`: exit 0, final `ok`; includes the browser regression checks. Wheel packaging skipped because pip is missing.
