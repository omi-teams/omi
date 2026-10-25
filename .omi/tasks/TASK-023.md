---
id: TASK-023
title: Skill group - squad workflow
status: in-progress
depends: TASK-022
scope: .omi/skills/workflow/**, .omi/skills/CATALOG.md, docs/research/_src/**, src/omi/template/dot-omi/skills/workflow/**, .omi/decisions.md
---
## Goal
Skills for discovery, planning and handoff, distilled per the TASK-020 table (Superpowers brainstorming/writing-plans, BMAD, GSD).

## Acceptance criteria
- [ ] Skills: `brainstorm-ac` (requirements to testable acceptance criteria), `task-brief` (short task brief for a fresh agent), `resume` (resume from checkpoint), `change-request` (scope change flow with PO decision), `lean-implementation` (YAGNI/stdlib-first rule for the engineer, adapted from Ponytail).
- [ ] Each passes `python -m omi skills --check`, cites a concrete squad step it serves, and records source, commit, file and license.
- [ ] Each is at most 2000 tokens; a candidate that duplicates `omi-idea` or `omi-task` is rejected and logged in decisions.
- [ ] Catalog regenerated; the template copy is identical.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-024
