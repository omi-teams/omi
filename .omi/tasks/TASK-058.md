---
id: TASK-058
title: Fresh omi init project works out of the box (catalog, test command, gitignore)
status: planned
depends: TASK-057
scope: src/omi/__init__.py, src/omi/template/**, tests/**, README.md
role: omi-agent-engineer
skills: []
workflow: omi-flow-bugfix
step:
---
## Goal
The three defects found by the TASK-057 sandbox (docs/research/omi-eval.md): a fresh `omi init` project runs `omi run` with a workflow without manual fixes.

## Acceptance criteria
- [ ] `omi init` writes `.omi/skills/CATALOG.md` (and the agents/workflows catalogs) so a task with a workflow runs without `omi skills` first.
- [ ] The test command needs no pytest by default: `"test"` in config if set, else pytest only when it is importable, else each `tests/test_*.py` run as a script; the template config documents the `"test"` key.
- [ ] `omi init` adds a `.gitignore` with `__pycache__/` (never overwrites an existing one; appends the line if missing), so the agent's own test run is not reported OUT OF SCOPE.
- [ ] A test does a fresh `omi init` in a temp dir and checks all three; `python tests/test_omi.py` passes.

## Checkpoint
Done:
Not done:
Tests:
Next:
