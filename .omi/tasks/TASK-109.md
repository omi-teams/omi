---
id: TASK-109
title: omi step approve, reopen after CI failure, task ID in PR titles
status: planned
depends: TASK-108
plan: PLAN-005
scope: src/omi/tasks.py, src/omi/cli.py, src/omi/template/dot-claude/skills/omi-task/SKILL.md, .claude/skills/omi-task/SKILL.md, tests/test_omi.py, README.md
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
Pilot gaps G5, G6 and G9 (found in TASK-107: CI fails after accept and `omi step back` cannot reopen a completed workflow): a PO approval is recorded by a command in the right place, and every squash commit names its task.

## Acceptance criteria
- [ ] `omi step <ID> approve "<PO words>"` writes `PO approval <current step>: <words>` under `## Steps` of the authoritative task file (state in detached mode), refuses when the current step is not a `po` gate, and commits like other step changes.
- [ ] `omi step <ID> reopen --why "<reason>"` on a completed workflow restarts its last write step, logs the reason under `## Steps`, and makes the po gate need a fresh approval line; refused while a step is running.
- [ ] The omi-task skill (template and repo copy) uses `omi step <ID> approve` and creates PRs with `--title "<type>: <title> (<ID>)"` instead of `--fill`, and on red CI after accept uses `omi step <ID> reopen`.
- [ ] Unit tests cover approve in in-repo and detached mode and the refusal; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
