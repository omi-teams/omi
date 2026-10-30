---
id: TASK-125
title: omi board v2 - colour, workflow diagram and task tree
status: planned
depends: TASK-115, TASK-124
plan: PLAN-006
scope: src/omi/board/web/**, tests/test_board_web.py, .omi/tasks/TASK-125.md, .omi/tasks/TASK-125-mockup/**
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
The board looks livelier, draws the workflow as a diagram and lists tasks as a tree (milestone > epic > FR/NFR > task) with status rolled up from children, like GitHub Projects with sub-issues.

## Acceptance criteria
- [ ] A new mockup in `.omi/tasks/TASK-125-mockup/` (plain HTML, desktop and 390 px) is approved by the PO before build; the build matches it.
- [ ] Richer colour: each status and each type has its own colour token (light and dark mode), always paired with text or an icon (never colour alone), text contrast at least 4.5:1.
- [ ] The task page draws the workflow as a diagram (steps as nodes with arrows, PO gates marked, current step highlighted, done steps marked) from the API's workflow steps; it stays readable at 360 px.
- [ ] The dashboard has a tree view of tasks: expand/collapse per parent (native, keyboard operable), type badge, derived status chip and a done/total progress bar per parent, from the TASK-124 API fields.
- [ ] State text still goes in via `textContent` only; no external script, font or CDN; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
