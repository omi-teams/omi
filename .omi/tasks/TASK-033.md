---
id: TASK-033
title: Workflows - feature, feature-ui, feature-sensitive
status: planned
depends: TASK-032, TASK-029, TASK-030
scope: .omi/workflows/**, src/omi/template/dot-omi/workflows/**, .omi/decisions.md
---
## Goal
The default build path and its two heavier variants.

## Acceptance criteria
- [ ] `omi-flow-feature`: plan, engineer, reviewer, PO acceptance. `omi-flow-feature-ui`: adds designer-ui before and qa-tester after. `omi-flow-feature-sensitive`: adds architect before and security-reviewer after.
- [ ] Each states when to use (and why not the lighter one), model/effort per step, the review-fail rule (2 fails -> escalate to opus/architect, then stop and ask the PO), and the PO gates.
- [ ] Each passes `omi workflows --check`; catalog regenerated; template copy identical.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-034
