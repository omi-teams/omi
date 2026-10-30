---
id: TASK-134
title: Task phase derived from the current workflow step
status: in-progress
depends: TASK-115
plan: PLAN-006
scope: src/omi/project/**, src/omi/app/cli.py, src/omi/board/data.py, tests/test_omi.py, tests/test_board.py, .omi/tasks/TASK-134.md
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
At a glance the PO sees which phase and step every task is in, the same set for every workflow, computed from the task's `status`, `step` and workflow definition, with no new field to keep in sync by hand.

## Acceptance criteria
- [ ] One function derives the phase: `status: planned` -> Chưa bắt đầu; `blocked` -> Bị chặn; `done` -> Xong; otherwise from the current step: gate `po` -> Chờ PO; role `coordinator` -> Lên kế hoạch; designer-ui/architect/researcher -> Thiết kế; engineer/docs-writer/devops -> Đang làm; reviewer/security-reviewer -> Đang review; qa-tester -> Đang QA. Unknown role, missing workflow or empty step falls back to Đang làm. Stored task fields and the status enum stay unchanged.
- [ ] Alongside the phase: step position `N/M` with the step id, and the review round (count of review FAIL reports + 1) while in a review or qa step.
- [ ] `omi status` shows `[<phase>] TASK-NNN title` and a second line `bước N/M <step> · vòng R · <tool> <model>/<effort>` plus a compact step strip (done steps ✓, current in brackets), e.g. `plan ✓ design ✓ build ✓ [review] qa · accept`.
- [ ] The board API returns `phase` (stable English key plus Vietnamese label), `step_index`, `step_count` and `review_round` per task (read-only).
- [ ] Tests cover every mapping rule, the fallbacks and the round count; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
