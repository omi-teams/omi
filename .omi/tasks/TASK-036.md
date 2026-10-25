---
id: TASK-036
title: Workflows - change-request, incident
status: in-progress
depends: TASK-032, TASK-029
scope: .omi/workflows/**, src/omi/template/dot-omi/workflows/**, .omi/decisions.md, tests/**
role: omi-agent-engineer
skills: []  # writes markdown workflows; step build adds omi-skill-lean-implementation
workflow: omi-flow-feature
step:
---
## Goal
Two workflows exist for work that goes off-plan: a change request after a task was approved, and an incident after a release or gate broke.

### Brief
- Create `.omi/workflows/omi-flow-change-request.md` and `.omi/workflows/omi-flow-incident.md`; copy both, byte-identical, to `src/omi/template/dot-omi/workflows/`.
- Copy the layout of `.omi/workflows/omi-flow-feature.md`: frontmatter `id`, `summary`, `steps:` lines `- id | role | skills | input | output | gate | stop`; body sections When to use / Use instead / Models / Stop conditions / Review-fail rule / PO gates. At most 2000 tokens each.
- Step skills from `.omi/skills/CATALOG.md`: change-request uses `omi-skill-change-request`; incident uses `omi-skill-incident`, `omi-skill-rollback` and `omi-skill-debug-root-cause` on the matching steps.
- Regenerate with `python -m omi workflows`; check with `python -m omi workflows --check`; tests: `python3 tests/test_omi.py` (the workflow count there is derived, no edit expected).

## Acceptance criteria
- [ ] `omi-flow-change-request`: impact on tasks and cost, options + one recommendation, PO decision recorded in decisions.md, then replan; no work starts before the decision.
- [ ] `omi-flow-incident`: contain, diagnose, hotfix or rollback, postmortem note; the production merge stays a PO gate.
- [ ] Each passes `python -m omi workflows --check`; `CATALOG.md` regenerated in both copies; `diff -r .omi/workflows src/omi/template/dot-omi/workflows` is empty.
- [ ] change-request: its decide step has gate `po`; incident: the production merge step has gate `po` and the hotfix step gate `review`.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-037
