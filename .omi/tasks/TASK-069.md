---
id: TASK-069
title: Add references a task names with refs, passed to agents as paths
status: planned
depends: TASK-068
scope: src/omi/__init__.py, tests/**, src/omi/template/**, .omi/references/**, .omi/tasks/_template.md, AGENTS.md
role: omi-agent-engineer
skills: []
tool:
workflow: omi-flow-feature
step:
---
## Goal
References in `.omi/references/<id>.md` (frontmatter `id, summary`) are listed in a catalog; a task names them with `refs: [...]` and the agent gets their paths to read when needed, outside any budget. Spec: `docs/specs/template-kinds.md` (References).

## Acceptance criteria
- [ ] `python -m omi references` validates each reference (id = file name, summary) and writes `.omi/references/CATALOG.md`.
- [ ] `omi run` adds the paths of the task's `refs` to the prompt under "References (read when needed)"; an unknown ref or one missing from the catalog stops the run with a clear message. Tested.
- [ ] `refs:` is in `.omi/tasks/_template.md` (root and template) and is Coordinator-owned frontmatter like `skills`.
- [ ] The template ships references `postgres-conventions` and `nextjs-app-router` and the catalog; `omi init` creates them. Tested.
- [ ] Template and root `AGENTS.md` mention references in one line each.
- [ ] All tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
