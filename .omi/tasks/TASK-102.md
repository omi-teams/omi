---
id: TASK-102
title: Bump omi to 0.4.0
status: in-progress
depends: TASK-101
plan: PLAN-004
scope: pyproject.toml, README.md, tests/test_omi.py, .omi/version, src/omi/template_shas.json
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
Release prep for PLAN-004, as in TASK-095.

## Acceptance criteria
- [ ] `omi --version` prints 0.4.0; `.omi/version` is 0.4.0; 0.4.0 template shas recorded; README documents detached mode in at most 15 lines.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:
