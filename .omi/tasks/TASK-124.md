---
id: TASK-124
title: Task hierarchy - type, parent and rolled-up status
status: planned
depends: TASK-115
plan: PLAN-007
scope: src/omi/project/**, src/omi/app/cli.py, src/omi/board/data.py, src/omi/template/**, .omi/tasks/_template.md, tests/test_omi.py, tests/test_board.py, .omi/tasks/TASK-124.md
role: omi-agent-engineer
skills: []
refs: []
tool:
model:
effort:
step_settings:
workflow: omi-flow-feature
step:
---
## Goal
Task files can form a tree like GitHub sub-issues (milestone > epic > FR/NFR > task), and a parent's status is computed from its children, so `omi status` and the board show the whole structure with consistent status.

## Acceptance criteria
- [ ] Task frontmatter gains optional `type: milestone|epic|fr|nfr|task` (default `task`) and `parent: <TASK-ID>`; the task template (repo and `src/omi/template`) documents both. Existing task files without them keep working unchanged; plans (`plan:`) stay as they are.
- [ ] Validation rejects an unknown `type`, a missing parent ID and a cycle, with a clear message naming the task.
- [ ] A task with children has a derived status: `done` if all children are done; `blocked` if any child is blocked; `planned` if all are planned; otherwise `in-progress`. Its own `status:` field is ignored and the derivation is recursive.
- [ ] Items with children are never suggested as the next task or runnable with `omi run`; `omi status` shows the tree indented with derived status and done/total counts per parent.
- [ ] The board API returns each task's `type`, `parent`, `children` and derived status (read-only, no writes); `tests/test_board.py` covers a 3-level tree.
- [ ] Tests cover defaults, validation errors and each status-derivation rule; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
