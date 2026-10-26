---
id: TASK-039
title: Carry-overs - skill fixes, test fix, review of unreviewed roles and commits
status: in-progress
depends: TASK-042, TASK-023, TASK-024, TASK-025, TASK-026, TASK-029, TASK-030, TASK-031
scope: .omi/agents/**, .omi/skills/**, src/omi/template/**, .claude/skills/**, tests/**
role: omi-agent-engineer
skills: []
workflow: omi-flow-feature
step:
---
## Goal
Close the review carry-overs left by earlier tasks. The baseline evaluation moved to TASK-057 (PO, 2026-10-26).

## Acceptance criteria
- [ ] `omi-skill-data-review`: fix the contradiction ("stop at the first group with blocking findings, then continue" -> report blocking findings first, then continue), in `.omi/skills` and its template copy.
- [ ] `omi-skill-web-qa`: confirm the `npx playwright cli` fallback against the pinned upstream skill; fix or note the source.
- [ ] Audit (fresh instance, the reviewers were wrongly skipped, see decisions 2026-10-25) the 7 roles from TASK-029/030/031 and Coordinator commits 8bece61 (omi-task model-invocable), 94f3458 (omi-status pick-list), e7a1bfb (reviewer skip path rule): list findings in the Checkpoint and fix each real one in scope.
- [ ] `tests/test_omi.py` read-role Usage check: replace `not endswith("/1 |")` with an exact `-` cell assertion so a missing row fails.
- [ ] `python tests/test_omi.py` and `python -m omi skills --check` pass.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-057
