---
id: TASK-003
title: Add omi github to enforce PO-only merges with rulesets
status: in-progress
depends: TASK-002
scope: src/omi/__init__.py, tests/**, README.md
---
## Goal
One command configures GitHub so the squad can merge only into `development`, and only the PO (repo admin) can merge into `staging` and `main`.

## Acceptance criteria
- [ ] `omi github` creates `staging` from `main` if missing.
- [ ] Ruleset on `development`: PR required, required status check `test`, no force push or deletion.
- [ ] Ruleset on `staging`/`main`: PR required, check `test`, updates restricted with bypass only for the repository admin role.
- [ ] Re-running it updates the existing rulesets and creates no duplicates; it prints what changed.
- [ ] If the token lacks admin, it stops with a clear message and changes nothing.
- [ ] A test covers the payload that gets built (no network).

## Checkpoint
Unblocked: PO is making the repo public (Free plan has no rulesets on private repos) and granting admin. Running `omi github` for real is the Coordinator's step after merge.
Not done:
Tests:
Next:
