---
id: TASK-112
title: Group src/omi into subpackages without behaviour change
status: in-progress
depends: TASK-109
plan: PLAN-006
scope: src/omi/**, tests/**, .omi/rules/omi-modules.md, .omi/rules/CATALOG.md, pyproject.toml, .omi/tasks/TASK-112.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: opus
effort: high
step_settings:
workflow: omi-flow-refactor
step:
---
## Goal
The flat 18-module `src/omi` becomes a few subpackages by responsibility (for example state, worker, project, setup), so the board and later work land in a clear place. Behaviour, CLI and the `python -m omi` entry stay identical.

## Acceptance criteria
- [ ] Every module sits in a subpackage named for one responsibility; `attach` no longer lives in the upgrade module; `__init__.py` stays the package surface.
- [ ] `.omi/rules/omi-modules.md` describes the new layout and layer order; `python -m omi rules` regenerates the catalog.
- [ ] Same test suite passes before and after with only import-path and patch-target edits; template files and `template_shas.json` unchanged; `pip install .` still ships the template.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:
