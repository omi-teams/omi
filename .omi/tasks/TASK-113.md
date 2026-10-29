---
id: TASK-113
title: Board data layer: state to JSON-ready dicts
status: planned
depends: TASK-112
plan: PLAN-006
scope: src/omi/board/__init__.py, src/omi/board/data.py, tests/test_omi.py
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
Backend half of the board: pure functions that read `$OMI_STATE` into dicts for the home page, a project dashboard and a task detail, reusing omi's task, plan and usage parsers.

## Acceptance criteria
- [ ] `projects()` lists `projects/*` with active plan progress, task counts by status and the PO-waiting count.
- [ ] `project(name)` returns PO-waiting items (open po gate, blocked, next task, `Next:` of in-progress tasks), plans, kanban columns, recent activity from `## Steps`/`## Reports`, latest decisions, usage totals per task and model with review rounds, and sync status (ahead/behind, last commit, dirty).
- [ ] `task(name, id)` returns frontmatter, Goal, criteria with ticks, Checkpoint, Steps, Reports, Usage.
- [ ] Names and IDs are validated; any resolved path outside `$OMI_STATE` raises; nothing is written.
- [ ] Unit tests on a temporary state repo cover each function and the path refusal; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
