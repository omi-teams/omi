---
id: TASK-136
title: Plans whose tasks are all done show as done
status: in-progress
depends:
plan: PLAN-007
scope: src/omi/board/**, src/omi/project/tasks.py, src/omi/app/cli.py, tests/test_board.py, tests/test_tasks.py, tests/test_content.py, .omi/tasks/TASK-136.md
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature
step:
---
## Goal
A plan with at least one task and every task `done` is shown as done in `omi status` and on the board, instead of `active`, without editing the plan file.

## Acceptance criteria
- [ ] One function derives a plan's shown status: `done` when it has tasks and all are `done`; otherwise the stored `status:`. The plan file is never rewritten.
- [ ] `omi status` lists done plans after active ones (or folds them into one `done plans: PLAN-002..006` line); the board's project list shows only plans that are not done, and the project view marks done plans.
- [ ] A plan with no tasks keeps its stored status.
- [ ] Tests cover all done, partly done, no tasks and a stored `status: done`; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
