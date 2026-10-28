---
id: TASK-092
title: Bump omi to 0.3.1
status: planned
depends: TASK-089, TASK-090, TASK-091
plan: PLAN-002
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
Release prep for PLAN-002: version 0.3.1 everywhere `omi --version` and the rc tag read it, as in TASK-088.

## Acceptance criteria
- [ ] `omi --version` prints 0.3.1; `.omi/version` is 0.3.1; 0.3.1 template shas recorded.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next: after merge: omi-release (rc), PO merges staging, then promote + tag v0.3.1; then `/omi-upgrade` in omi-board.
