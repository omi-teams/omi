---
id: TASK-095
title: Bump omi to 0.3.2
status: planned
depends: TASK-093, TASK-094
plan: PLAN-003
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
Release prep for PLAN-003: version 0.3.2 everywhere `omi --version` and the rc tag read it, as in TASK-092.

## Acceptance criteria
- [ ] `omi --version` prints 0.3.2; `.omi/version` is 0.3.2; 0.3.2 template shas recorded.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:
