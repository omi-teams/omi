---
id: TASK-030
title: Roles - verification (security-reviewer, qa-tester)
status: done
depends: TASK-028, TASK-024
scope: .omi/agents/**, src/omi/template/dot-omi/agents/**, .omi/decisions.md
---
## Goal
Two independent read-only roles that give evidence beyond the general reviewer.

## Acceptance criteria
- [ ] `omi-agent-security-reviewer` (sonnet, medium; opus for auth, payment or secrets): diff security review and CI/agent workflow audit; every finding has location, reason and how it was verified; default skills `omi-skill-diff-security-review`, `omi-skill-ci-workflow-audit`.
- [ ] `omi-agent-qa-tester` (sonnet, medium): runs the acceptance criteria as checks and reports pass/fail with evidence (test output, screenshots for web via the qa-web skill); never edits code.
- [ ] Each role states when to use / not use, output format (at most 8 lines), stop and escalate conditions, tools allowed and sources.
- [ ] Skipped for docs-only or `.omi/`-only changes, as the reviewer is.
- [ ] Catalog regenerated; template copy identical.

## Checkpoint
Done: both roles, catalog regenerated (7 roles), template copy identical
Not done: -
Tests: none in scope; catalog generator ran OK
Next: TASK-031

## Usage
| role | model | effort | input | output | cache | duration |
|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 16 | 2979 | 172944 | 30s |
