---
id: TASK-033
title: Workflows - feature, feature-ui, feature-sensitive
status: in-progress
depends: TASK-032, TASK-029, TASK-030
scope: .omi/workflows/**, src/omi/template/dot-omi/workflows/**, .omi/decisions.md, src/omi/__init__.py, tests/**
---
## Goal
The default build path and its two heavier variants.

## Acceptance criteria
- [ ] `omi-flow-feature`: plan, engineer, reviewer, PO acceptance. `omi-flow-feature-ui`: adds designer-ui before and qa-tester after. `omi-flow-feature-sensitive`: adds architect before and security-reviewer after.
- [ ] Each states when to use (and why not the lighter one), model/effort per step, the review-fail rule (2 fails -> escalate to opus/architect, then stop and ask the PO), and the PO gates.
- [ ] Each passes `omi workflows --check`; catalog regenerated; template copy identical.

- [ ] Carry-over from the TASK-032 review: validate `<TASK-ID>` in `omi step` against `^[A-Za-z0-9_-]+$` (no path traversal); only count a `PO approval <step>:` line inside `## Steps`; the default workflow is `omi-flow-feature` (the TASK-032 AC said `feature`), so `omi step` works only once this task adds it.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-034
