---
id: TASK-115
title: omi board frontend
status: in-progress
depends: TASK-114
plan: PLAN-006
scope: src/omi/board/web/**, pyproject.toml, tests/test_board_web.py, tests/test_omi.py, .omi/tasks/TASK-115.md
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature-ui
step:
---
## Goal
Plain HTML/CSS/JS pages for home, project dashboard and task detail, in Vietnamese, calling the JSON API.

## Acceptance criteria
- [ ] Home, dashboard (PO-waiting, plans, kanban, activity, decisions, usage, sync) and task detail render from the API; auto-refresh every 30 s with a toggle.
- [ ] State text is inserted with `textContent` only, never `innerHTML`; no external script, font or CDN.
- [ ] `pip install .` ships `board/web/*` (package data); a test checks the files are in the installed package.
- [ ] Readable at 360 px width and keyboard navigable; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
