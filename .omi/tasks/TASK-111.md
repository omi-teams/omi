---
id: TASK-111
title: Bump omi to 0.4.1
status: planned
depends: TASK-110
plan: PLAN-005
scope: pyproject.toml, README.md, tests/test_omi.py, .omi/version, src/omi/template_shas.json
role: omi-agent-engineer
skills: []
refs: []
tool:
model:
effort:
step_settings:
workflow: omi-flow-feature
step:
---
## Goal
Release prep for PLAN-005, as in TASK-102.

## Acceptance criteria
- [ ] `omi --version` prints 0.4.1; `.omi/version` is 0.4.1; 0.4.1 template shas recorded.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:
