---
id: TASK-050
title: Move role default skills onto workflow steps
status: in-progress
depends: TASK-036
scope: .omi/agents/**, src/omi/template/dot-omi/agents/**, .omi/workflows/**, src/omi/template/dot-omi/workflows/**, tests/**
role: omi-agent-engineer
skills: []  # step build adds omi-skill-lean-implementation
workflow: omi-flow-feature
step: build
---
## Goal
No role carries default skills; each workflow step names the skills its work needs, so a run loads only those and no role blocks the 3-skill budget.

### Brief
- Set `skills: []` in all 9 `.omi/agents/omi-agent-*.md` (root and `src/omi/template/dot-omi/agents/`, identical); drop or reword body lines that say a role "defaults to" skills; regenerate `.omi/agents/CATALOG.md` with `python -m omi agents` and copy it to the template.
- Move the skills onto steps (both workflow copies identical, `python -m omi workflows` then copy `CATALOG.md`):
  - `omi-flow-feature-ui` design step: `omi-skill-ui-direction, omi-skill-ui-a11y-review`; qa step: `omi-skill-web-qa`.
  - `omi-flow-feature-sensitive` security step: `omi-skill-diff-security-review, omi-skill-ci-workflow-audit`.
  - `omi-flow-incident`: `contain` and `merge-prod` move from `coordinator` to `omi-agent-devops` (skills `omi-skill-incident` and `omi-skill-rollback, omi-skill-release-checklist`); keep the `po` gate on `merge-prod` (the PO still approves the production merge; devops never pushes to `staging`/`main`).
- Tests: `python3 tests/test_omi.py`; fix only tests that relied on a real role's default skills.

## Acceptance criteria
- [ ] Every role file has `skills: []`; agents catalog regenerated; template copies identical (`diff -r`).
- [ ] The step skills above are declared; `python -m omi workflows --check` passes; workflow template copies identical.
- [ ] `python -m omi skills check` passes for every `.omi/tasks/TASK-*.md` with status planned.
- [ ] `python3 tests/test_omi.py` passes.

## Checkpoint
Done: all 9 roles skills: [], step skills moved, incident contain/merge-prod -> devops, catalogs regenerated, template copies identical.
Not done: none.
Tests: python3 tests/test_omi.py ok; workflows --check ok; skills check ok for planned tasks.
Next: TASK-037

## Steps
- plan started 2026-10-25 22:17
- plan done 2026-10-25 22:17
- build started 2026-10-25 22:17

## Usage
| role | model | effort | input | output | cache | duration | skills read |
|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 14 | 2798 | 161346 | 58s | 1/1 omi-skill-lean-implementation |
