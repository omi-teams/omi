---
id: TASK-106
title: Repo rule for the src/omi module structure
status: in-progress
depends: TASK-104
plan: PLAN-004
scope: .omi/rules/omi-modules.md, .omi/rules/CATALOG.md
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
The module rules chosen in TASK-104 (decisions.md 2026-10-28) live only in decisions.md, which agents do not read. A rule in `.omi/rules` reaches every task whose scope touches `src/omi/*.py` through `omi run`, so PLAN-004 code follows the split without restating it per task. Repo-only: the template (`src/omi/template/**`) is not changed, user projects do not get it.

## Acceptance criteria
- [ ] `.omi/rules/omi-modules.md` with frontmatter `id`, `summary`, `applies: src/omi/*.py`, at most ~200 tokens, says: modules call each other as `from . import x` then `x.name(...)`, never `from .x import name`; imports only go down the layer order of the current graph, cli > run > hooks > docker > tasks/upgrade > workflows > catalogs > tools/creds/scope > core/github (no import inside a function to dodge a cycle); no module over ~600 lines; a new responsibility gets a new module; `__init__.py` stays the package surface; tests patch the defining module (`omi.<module>.<name>`).
- [ ] `.omi/rules/CATALOG.md` regenerated with `python -m omi rules`; `omi.catalogs.task_rules` picks the rule for `src/omi/run.py` and not for `tests/test_omi.py` (shown by the command output in the report).
- [ ] All tests pass on the Linux worker and on the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:
