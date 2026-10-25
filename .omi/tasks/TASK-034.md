---
id: TASK-034
title: Workflows - bugfix, refactor
status: done
depends: TASK-032
scope: .omi/workflows/**, src/omi/template/dot-omi/workflows/**, .omi/decisions.md, tests/**
role: omi-agent-engineer
skills: []  # writes markdown workflows; the step skills below go into the workflow files
---
## Goal
Workflows for changing existing code safely.

## Acceptance criteria
- [x] `omi-flow-bugfix`: reproduce with a failing test, fix the root cause (grep all callers), regression test, reviewer.
- [x] `omi-flow-refactor`: tests green before, behaviour unchanged, tests green after, reviewer; no scope growth.
- [x] Each has PO gates, stop conditions and the review-fail rule; passes `--check`; catalog regenerated; template copy identical.
- [x] Step skills: bugfix fix step uses `omi-skill-debug-root-cause`; refactor review step uses `omi-skill-simplify-review`. Follow the layout of `.omi/workflows/omi-flow-feature.md`.

## Checkpoint
Done: omi-flow-bugfix and omi-flow-refactor (+ template copies, catalog regenerated, `workflows --check` ok, template identical).
Not done: nothing.
Tests: PYTHONPATH=src python3 tests/test_omi.py ok; workflows count assertion now derived from wf glob.
NEEDS SCOPE granted: tests/** added. Make the `workflows ok (N checked)` assertion count-independent (e.g. the number of template workflow files), so later workflow tasks do not break it.
Next: TASK-035

## Usage
| role | model | effort | input | output | cache | duration | skills read |
|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 14 | 3899 | 158215 | 49s | - |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 10 | 863 | 93352 | 21s | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 8 | 1492 | 97922 | 28s | - |
