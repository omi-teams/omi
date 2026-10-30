---
id: TASK-133
title: omi board weekly report export
status: planned
depends: TASK-126
plan: PLAN-007
scope: src/omi/board/**, tests/test_board.py, tests/test_board_web.py, .omi/tasks/TASK-133.md
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
The PO downloads a Markdown report of the last 7 days to share with stakeholders.

## Acceptance criteria
- [ ] A "Tải báo cáo tuần" button builds Markdown client-side (Blob download): tasks done, in progress, blocked, decisions, tokens and cost (TASK-126), next tasks; Vietnamese.
- [ ] Tests check the generated Markdown on a fixture.
- [ ] The board stays read-only; state text via `textContent` only; no external script, font or CDN; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
