---
id: TASK-025
title: Skill group - delivery and operations
status: planned
depends: TASK-022
scope: .omi/skills/delivery-ops/**, src/omi/template/dot-omi/skills/delivery-ops/**, .omi/decisions.md
---
## Goal
Skills for release, rollback, incidents and the Windows/Docker environment, from OMI's own experience and primary docs (not a summary repo).

## Acceptance criteria
- [ ] Skills: `release-checklist`, `rollback`, `incident`, `docker-worker-pitfalls`, `windows-powershell`.
- [ ] Each cites a concrete squad step or past problem (TASK-006, TASK-010, TASK-015, TASK-018) and the primary doc it is based on.
- [ ] Each passes `--check`, is at most 2000 tokens, and records source and license.
- [ ] Catalog regenerated; the template copy is identical.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-026
