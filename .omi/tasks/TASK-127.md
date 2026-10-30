---
id: TASK-127
title: omi board PO inbox with notifications
status: planned
depends: TASK-123, TASK-125
plan: PLAN-007
scope: src/omi/board/**, tests/test_board.py, tests/test_board_web.py, .omi/tasks/TASK-127-mockup/**, .omi/tasks/TASK-127.md
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
Everything waiting for the PO sits in one inbox with its age and the exact command to type, and the browser notifies the PO when a new item arrives.

## Acceptance criteria
- [ ] A mockup in `.omi/tasks/TASK-127-mockup/` is PO-approved before build.
- [ ] Inbox items: PO gates (accept, design approval), NEEDS SCOPE, QUOTA stops, review FAIL x2 waiting for a decision; each shows task, what is asked, waiting since, and the command (e.g. `omi-task TASK-115`) with a copy button.
- [ ] Opt-in browser notification (Notification API, asked only after a click) when a new item appears via the TASK-123 version poll; title badge with the count.
- [ ] Tests cover item detection on fixtures and no duplicate notification for an existing item.
- [ ] The board stays read-only; state text via `textContent` only; no external script, font or CDN; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
