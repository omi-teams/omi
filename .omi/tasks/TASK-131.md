---
id: TASK-131
title: omi board dependency graph
status: planned
depends: TASK-124, TASK-125
plan: PLAN-007
scope: src/omi/board/**, tests/test_board.py, tests/test_board_web.py, .omi/tasks/TASK-131-mockup/**, .omi/tasks/TASK-131.md
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
A graph of task `depends` shows what blocks what and the critical path to the plan's end.

## Acceptance criteria
- [ ] A mockup in `.omi/tasks/TASK-131-mockup/` is PO-approved before build.
- [ ] Inline SVG layered layout (no library), nodes coloured by status with text labels, critical path highlighted, blocked tasks marked; clicking a node opens the task.
- [ ] A text list fallback for screen readers and widths under 768 px.
- [ ] Tests cover layering, cycle reporting and the critical path on fixtures.
- [ ] The board stays read-only; state text via `textContent` only; no external script, font or CDN; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
