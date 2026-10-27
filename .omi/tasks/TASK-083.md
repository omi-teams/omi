---
id: TASK-083
title: A task's own read role (e.g. the spike researcher) uses the task's tool, model and effort
status: planned
depends:
plan: PLAN-001
scope: src/omi/__init__.py, tests/test_omi.py, .omi/tasks/_template.md, src/omi/template/dot-omi/tasks/_template.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: sonnet
effort: medium
workflow: omi-flow-bugfix
step:
---
## Goal
`omi run` applies a task's `tool/model/effort` only to write roles (`src/omi/__init__.py` around `write = am["access"] == "write"`). In a spike the task's own `role:` is the read-only researcher, so TASK-081 (`tool: codex`) ran on claude. Fix it at that one place: the task's settings also apply when the role being run is the task's own `role:`. Other read roles (reviewer, security-reviewer) keep their own settings so review stays independent.

## Acceptance criteria
- [ ] `omi run <role> <ID>` where `<role>` equals the task's `role:` uses the task's `tool`, `model` and `effort` (then the role's, then defaults), for read roles too; `--tool/--model/--effort` still win.
- [ ] Running a read role that is not the task's `role:` (e.g. `omi-agent-reviewer` on an engineer task) still ignores the task's tool/model/effort.
- [ ] A regression test in `tests/test_omi.py` fails before the fix and passes after, covering both cases.
- [ ] The `tool:`/`model:` comments in both `_template.md` copies say "write role or the task's own role" instead of "write role only".

## Checkpoint
Done:
Not done:
Tests:
Next:
