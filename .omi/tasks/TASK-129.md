---
id: TASK-129
title: omi board filters, search and shareable links
status: planned
depends: TASK-125
plan: PLAN-007
scope: src/omi/board/**, tests/test_board.py, tests/test_board_web.py, .omi/tasks/TASK-129.md
role: omi-agent-engineer
skills: [omi-skill-ui-direction]
refs: []
tool:
model:
effort:
step_settings:
workflow: omi-flow-feature-ui
step:
---
## Goal
The PO finds any task fast: filter by status, type, plan and role, search by ID or title, and share the filtered view as a link.

## Acceptance criteria
- [ ] Filters and search run client-side on the loaded data and are kept in the URL hash; reloading or opening the link restores them.
- [ ] Keyboard: `/` focuses search, Esc clears it; an empty result shows a clear message and a reset button.
- [ ] Tests cover filter combinations and hash round-trip in the Node DOM tests.
- [ ] The board stays read-only; state text via `textContent` only; no external script, font or CDN; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
