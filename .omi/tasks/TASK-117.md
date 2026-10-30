---
id: TASK-117
title: Bump omi to 0.5.0
status: in-progress
depends: TASK-116, TASK-119
plan: PLAN-006
scope: pyproject.toml, README.md, tests/test_omi.py, tests/test_upgrade.py, .omi/version, src/omi/template_shas.json
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: haiku
effort: low
step_settings:
workflow: omi-flow-feature
step:
---
## Goal
Release prep for PLAN-006, as in TASK-102.

## Acceptance criteria
- [ ] `omi --version` prints 0.5.0; `.omi/version` is 0.5.0; 0.5.0 template shas recorded.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:
