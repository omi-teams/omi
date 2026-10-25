---
id: TASK-034
title: Workflows - bugfix, refactor
status: planned
depends: TASK-032
scope: .omi/workflows/**, src/omi/template/dot-omi/workflows/**, .omi/decisions.md
---
## Goal
Workflows for changing existing code safely.

## Acceptance criteria
- [ ] `bugfix`: reproduce with a failing test, fix the root cause (grep all callers), regression test, reviewer.
- [ ] `refactor`: tests green before, behaviour unchanged, tests green after, reviewer; no scope growth.
- [ ] Each has PO gates, stop conditions and the review-fail rule; passes `--check`; catalog regenerated; template copy identical.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-035
