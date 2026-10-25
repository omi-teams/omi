---
id: TASK-009
title: Pilot OMI on a real product from an empty folder
status: in-progress
depends: TASK-004, TASK-008
scope: docs/pilot.md
---
## Goal
Run the full journey on a real product idea and measure the cost: PO interventions, resumes and quota per task.

## Acceptance criteria
- [ ] `omi init` in an empty folder, then `omi-idea` produces an approved `docs/product.md` and a backlog.
- [ ] At least 2 tasks run through to merge into development, plus one staging candidate.
- [ ] `docs/pilot.md` records the token count per role, the number of PO interventions, and the problems found together with the tasks that fix them.

## Checkpoint
Done: PO chose `split-bill` (Python CLI that splits a group bill). Pilot repo: E:/Github/Orgs/omi-teams/omi-pilot-splitbill, GitHub omi-teams/omi-pilot-splitbill (public).
Not done: PO runs omi github, then /omi-idea, 2x /omi-task, /omi-release in a session in the pilot repo.
Problems so far: (1) omi-idea commits on main and creates development but never pushes; the Coordinator pushed by hand. (2) Order dependency: omi github must run after main is pushed, because the main ruleset then blocks the direct push.
Tests:
Next: after the pilot, measure tokens per role and PO interventions from ~/.claude/projects transcripts; write docs/pilot.md.
