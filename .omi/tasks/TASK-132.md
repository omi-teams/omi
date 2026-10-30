---
id: TASK-132
title: omi board task timeline
status: planned
depends: TASK-125
plan: PLAN-007
scope: src/omi/board/**, tests/test_board.py, tests/test_board_web.py, .omi/tasks/TASK-132.md
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
The task page shows what happened when: each step with duration, each review round with verdict, and the files changed.

## Acceptance criteria
- [ ] Timeline from `## Steps` timestamps and `## Reports` verdicts; step durations in Vietnamese format; running step shows elapsed time.
- [ ] Changed files from `git diff --name-only development...task/<ID>` when the branch exists (read-only git), else hidden.
- [ ] Tests cover parsing Steps/Reports on fixtures and a missing branch.
- [ ] The board stays read-only; state text via `textContent` only; no external script, font or CDN; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
