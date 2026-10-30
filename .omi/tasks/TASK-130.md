---
id: TASK-130
title: omi board health alerts
status: planned
depends: TASK-125
plan: PLAN-007
scope: src/omi/board/**, tests/test_board.py, tests/test_board_web.py, .omi/tasks/TASK-130.md
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
The dashboard warns early about stuck work.

## Acceptance criteria
- [ ] The API flags: in-progress with no Steps/commit activity for more than `board_stale_days` (config, default 3), 2+ review FAILs, task branch more than 20 commits behind development, depends on a blocked task.
- [ ] Alerts show as a banner list with the task, reason and suggested action; none shows nothing.
- [ ] Tests cover each rule on fixtures, including the config default.
- [ ] The board stays read-only; state text via `textContent` only; no external script, font or CDN; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
