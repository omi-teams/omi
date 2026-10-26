---
id: TASK-057
title: Final evaluation of skills, roles and workflows against baselines
status: in-progress
depends: TASK-039
scope: docs/research/omi-eval.md, .omi/agents/**, .omi/skills/**, .omi/workflows/**, .omi/decisions.md
role: omi-agent-engineer
skills: []
workflow: omi-flow-spike
step:
---
## Goal
One evaluation for everything, using real usage numbers. Keep only what earns its place. Estimated ~55 runs (2026-10-26); the PO picks full or lean scope before it starts.

## Acceptance criteria
- [ ] Every skill and every role is covered by a scenario inside the workflow runs below, each also run once with a plain prompt (no skill/role) as baseline; one baseline per skill or role, not per workflow.
- [ ] One scenario per workflow family (feature, bugfix, docs-only, change-request, incident, release), run in the Docker worker; record tokens, review rounds, steps skipped and problems.
- [ ] A skill, role or step that does not beat its baseline on correctness, tokens or review rounds is removed or reworked; decisions logged with the numbers.
- [ ] Report to the PO: total default context added by skills, roles and workflows.

## Checkpoint
Done:
Not done:
Tests:
Next:
