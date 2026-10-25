---
id: TASK-039
title: Final evaluation of skills, roles and workflows against baselines
status: planned
depends: TASK-042, TASK-023, TASK-024, TASK-025, TASK-026, TASK-029, TASK-030, TASK-031
scope: docs/research/omi-eval.md, .omi/agents/**, .omi/skills/**, .omi/workflows/**, .omi/decisions.md
---
## Goal
One evaluation for everything, using the real usage numbers from TASK-040. Keep only what earns its place.

## Acceptance criteria
- [ ] Every skill and every role is covered by a scenario inside the workflow runs below, each also run once with a plain prompt (no skill/role) as baseline; one baseline per skill or role, not per workflow.
- [ ] One scenario per workflow family (feature, bugfix, docs-only, change-request, incident, release), run in the Docker worker; record tokens, review rounds, steps skipped and problems.
- [ ] A skill, role or step that does not beat its baseline on correctness, tokens or review rounds is removed or reworked; decisions logged with the numbers.
- [ ] Report to the PO: total default context added by skills, roles and workflows.

- [ ] Carry-over from the TASK-026 review: fix the contradiction in `omi-skill-data-review` ("stop at the first group with blocking findings, then continue" -> report blocking findings first, then continue), and confirm the `npx playwright cli` fallback in `omi-skill-web-qa` against the pinned upstream skill.
- [ ] Unreviewed on merge (reviewer wrongly skipped, see decisions 2026-10-25): review the 7 roles from TASK-029/030/031 and the Coordinator commits 8bece61 (omi-task model-invocable), 94f3458 (omi-status pick-list), e7a1bfb (reviewer skip path rule).
- [ ] Carry-over from the TASK-049 review: `tests/test_omi.py` read-role Usage check uses `not endswith("/1 |")`; assert the exact `-` cell so a missing row fails.

## Checkpoint
Done:
Not done:
Tests:
Next: PO review, then release
