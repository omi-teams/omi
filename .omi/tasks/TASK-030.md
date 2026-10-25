---
id: TASK-030
title: Roles - verification (security-reviewer, qa-tester)
status: planned
depends: TASK-028, TASK-024
scope: .omi/agents/**, src/omi/template/dot-omi/agents/**, .omi/decisions.md
---
## Goal
Two independent read-only roles that give evidence beyond the general reviewer.

## Acceptance criteria
- [ ] `omi-security-reviewer` (sonnet, medium; opus for auth, payment or secrets): diff security review and CI/agent workflow audit; every finding has location, reason and how it was verified; default skills `omi-diff-security-review`, `omi-ci-workflow-audit`.
- [ ] `omi-qa-tester` (sonnet, medium): runs the acceptance criteria as checks and reports pass/fail with evidence (test output, screenshots for web via the qa-web skill); never edits code.
- [ ] Each role states when to use / not use, output format (at most 8 lines), stop and escalate conditions, tools allowed and sources.
- [ ] Skipped for docs-only or `.omi/`-only changes, as the reviewer is.
- [ ] Catalog regenerated; template copy identical.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-031
