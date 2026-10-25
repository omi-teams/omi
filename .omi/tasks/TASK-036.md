---
id: TASK-036
title: Workflows - change-request, incident
status: planned
depends: TASK-032, TASK-029
scope: .omi/workflows/**, src/omi/template/dot-omi/workflows/**, .omi/decisions.md
---
## Goal
Workflows for things that go off-plan.

## Acceptance criteria
- [ ] `change-request`: impact on tasks and cost, options + one recommendation, PO decision recorded in decisions.md, then replan; no work starts before the decision.
- [ ] `incident`: contain, diagnose, hotfix or rollback, postmortem note; the production merge stays a PO gate.
- [ ] Each passes `--check`; catalog regenerated; template copy identical.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-037
