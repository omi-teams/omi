---
id: TASK-009
title: Pilot OMI on a real product from an empty folder
status: done
depends: TASK-004, TASK-008
scope: docs/pilot.md
---
## Goal
Run the full journey on a real product idea and measure the cost: PO interventions, resumes and quota per task.

## Acceptance criteria
- [x] `omi init` in an empty folder, then `omi-idea` produces an approved `docs/product.md` and a backlog.
- [x] At least 2 tasks run through to merge into development, plus one staging candidate.
- [x] `docs/pilot.md` records the token count per role, the number of PO interventions, and the problems found together with the tasks that fix them.

## Checkpoint
Done: pilot run, results in docs/pilot.md; fixes planned as TASK-014.
Tests: n/a (docs only)
Next: PO does UAT on pilot PR #3.
