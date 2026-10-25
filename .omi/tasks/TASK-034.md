---
id: TASK-034
title: Workflows - bugfix, refactor
status: in-progress
depends: TASK-032
scope: .omi/workflows/**, src/omi/template/dot-omi/workflows/**, .omi/decisions.md
role: omi-agent-engineer
skills: []  # writes markdown workflows; the step skills below go into the workflow files
---
## Goal
Workflows for changing existing code safely.

## Acceptance criteria
- [ ] `omi-flow-bugfix`: reproduce with a failing test, fix the root cause (grep all callers), regression test, reviewer.
- [ ] `omi-flow-refactor`: tests green before, behaviour unchanged, tests green after, reviewer; no scope growth.
- [ ] Each has PO gates, stop conditions and the review-fail rule; passes `--check`; catalog regenerated; template copy identical.
- [ ] Step skills: bugfix fix step uses `omi-skill-debug-root-cause`; refactor review step uses `omi-skill-simplify-review`. Follow the layout of `.omi/workflows/omi-flow-feature.md`.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-035
