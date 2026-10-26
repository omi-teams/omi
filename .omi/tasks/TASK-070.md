---
id: TASK-070
title: Add plans that group tasks, with progress in omi status
status: planned
depends: TASK-069
scope: src/omi/__init__.py, tests/**, src/omi/template/**, .omi/plans/**, .omi/tasks/_template.md, AGENTS.md
role: omi-agent-engineer
skills: []
tool: codex  # PO: try codex on simpler tasks
workflow: omi-flow-feature
step:
---
## Goal
Plans in `.omi/plans/PLAN-NNN.md` (frontmatter `id, title, status: active|done`, then goal and done criteria) group tasks that set `plan: PLAN-NNN`; `omi status` shows each active plan's progress. Spec: `docs/specs/template-kinds.md` (Plans).

## Acceptance criteria
- [ ] `python -m omi plans` validates each plan (id = file name, title, status in active|done) and writes `.omi/plans/CATALOG.md`.
- [ ] A task whose `plan` names an unknown plan fails `omi run` with a clear message. Tested.
- [ ] `omi status` prints one line per active plan: `PLAN-NNN title: done x/y` counted from tasks with that `plan`. Tested.
- [ ] `plan:` is in `.omi/tasks/_template.md` (root and template) and is Coordinator-owned frontmatter.
- [ ] The template ships `PLAN-000.md` (an example) and the catalog; `omi init` creates them. Tested.
- [ ] Template and root `AGENTS.md` mention plans in one line each.
- [ ] All tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
