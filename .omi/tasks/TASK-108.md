---
id: TASK-108
title: Warn when an attached repo still has in-repo omi files
status: planned
depends: TASK-107
plan: PLAN-005
scope: src/omi/upgrade.py, src/omi/cli.py, tests/test_omi.py, README.md
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
Pilot gap G4: the PO sees that in-repo `.omi/`, `AGENTS.md` or `.claude/` in an attached code repo are ignored.

## Acceptance criteria
- [ ] `omi attach` and `omi status` in detached mode print one `WARN: in-repo omi files ignored (detached): <paths>` line when the code repo tracks `.omi/`, `AGENTS.md` or `.claude/`; nothing is printed otherwise; no migration.
- [ ] In-repo mode output is unchanged.
- [ ] Unit tests cover warn and no-warn cases; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
