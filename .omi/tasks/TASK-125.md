---
id: TASK-125
title: omi board v2 - colour, workflow diagram and task tree
status: planned
depends: TASK-115, TASK-124, TASK-134
plan: PLAN-006
scope: src/omi/board/web/**, tests/test_board_web.py, src/omi/app/cli.py, tests/test_cli.py, tests/test_init.py, tests/test_tools.py, .omi/tasks/TASK-125.md, .omi/tasks/TASK-125-mockup/**
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
- [ ] Kanban columns follow the TASK-134 phases (Chưa bắt đầu, Lên kế hoạch, Thiết kế, Đang làm, Đang review, Đang QA, Chờ PO, Bị chặn, Xong); each card shows a phase chip, `bước N/M` and the review round; empty columns collapse.
- [ ] From TASK-115 QA: a done task shows every workflow step as done (✓), including the last one; the Usage table on the task page fits its card without horizontal scrolling (e.g. a stacked layout).
- [ ] From TASK-134 review: the first `omi status` line is exactly `[<phase>] TASK-NNN title` (drop ` (step: X)`, update tests/test_init.py and tests/test_tools.py); a step id missing from the workflow prints `bước ?/M` instead of `bước 0/M`; tests/test_cli.py asserts the `bước N/M ... · vòng R · tool model/effort` line and the step strip.
- [ ] State text still goes in via `textContent` only; no external script, font or CDN; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
