---
id: TASK-037
title: Workflows - release and promote (migrate omi-release)
status: planned
depends: TASK-032, TASK-031
scope: .omi/workflows/**, src/omi/template/dot-omi/workflows/**, .claude/skills/omi-release/**, src/omi/template/dot-claude/skills/omi-release/**, tests/**
---
## Goal
Express the existing release flow as workflows without changing its behaviour.

## Acceptance criteria
- [ ] `release` and `promote` workflows reproduce every step and PO gate of the current omi-release skill (merges into staging/main stay with the PO).
- [ ] `omi-release` becomes a thin entry that starts the workflow; no step of the old flow is lost (checked against the old file in the review).
- [ ] `python tests/test_omi.py` passes; template copy identical.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-038
