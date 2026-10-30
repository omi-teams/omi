---
id: TASK-135
title: omi board shows the in-repo project it is started from
status: planned
depends: TASK-115
plan: PLAN-007
scope: src/omi/board/**, tests/test_board.py, tests/test_board_server.py, .omi/tasks/TASK-135.md
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
`omi board` started inside an in-repo project (its own `.omi/`, not attached) lists that project next to the `$OMI_STATE` projects, so the PO can see repos like omi itself without a detached copy.

## Acceptance criteria
- [ ] Started in an in-repo project, `/api/projects` includes it (name = repo folder name) with plans, kanban, tasks and decisions read from its `.omi/`; started anywhere else, the list is unchanged.
- [ ] Path safety stays: every resolved path must sit under `$OMI_STATE` or under that one in-repo root; traversal, symlinks or junctions pointing elsewhere still raise; nothing is written.
- [ ] A name clash with a `$OMI_STATE` project is resolved predictably (the in-repo one is listed once, with a marker such as `"mode": "in-repo"`), and the sync block says `in-repo` instead of ahead/behind of the state repo.
- [ ] Tests on a temporary in-repo project and a temporary state cover listing, project and task views, the clash and the path refusal; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
