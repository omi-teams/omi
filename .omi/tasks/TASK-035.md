---
id: TASK-035
title: Workflows - docs-only, spike
status: planned
depends: TASK-032, TASK-029, TASK-031
scope: .omi/workflows/**, src/omi/template/dot-omi/workflows/**, .omi/decisions.md
---
## Goal
The two cheapest paths.

## Acceptance criteria
- [ ] `docs-only`: docs-writer then PO check; no reviewer (CI still runs), matching the quota rule.
- [ ] `spike`: researcher produces a cited report in `docs/`, no product code, ends in a PO decision.
- [ ] Each passes `--check`; catalog regenerated; template copy identical.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-036
