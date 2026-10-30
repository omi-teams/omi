---
id: TASK-128
title: Automated browser QA for omi board
status: planned
depends: TASK-115
plan: PLAN-007
scope: src/omi/template/docker/Dockerfile, .github/workflows/ci.yml, tests/test_board_web.py, tests/board_screens/**, .omi/tasks/TASK-128.md
role: omi-agent-engineer
skills: []
refs: []
tool:
model:
effort:
step_settings:
workflow: omi-flow-feature-sensitive
step:
---
## Goal
Browser checks (360/390/768/1280 px, keyboard, a11y) run automatically in the worker and in CI instead of being skipped for missing Playwright.

## Acceptance criteria
- [ ] Playwright with Chromium is available in the worker image and in CI; image size growth is reported to the PO before merge.
- [ ] The existing skip-if-missing browser tests run in CI; screenshots of each page at each width are saved as CI artifacts.
- [ ] An axe-core (vendored, pinned) a11y check runs per page with zero serious or critical violations.
- [ ] A print stylesheet check: dashboard and task pages print without header controls.
- [ ] The board stays read-only; state text via `textContent` only; no external script, font or CDN; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
