---
id: TASK-111
title: Bump omi to 0.4.1
status: planned
depends: TASK-110, TASK-112
plan: PLAN-005
scope: pyproject.toml, README.md, tests/test_upgrade.py, tests/test_cli.py, .omi/version, src/omi/template_shas.json, src/omi/app/cli.py, .omi/tasks/TASK-111.md
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
- [ ] The CLI usage line for `step` lists `next|done|back|skip|approve|reopen` (wherever cli.py lives after TASK-112).
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:
