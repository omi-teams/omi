---
id: TASK-003
title: Add omi github to enforce PO-only merges with rulesets
status: done
depends: TASK-002
scope: src/omi/__init__.py, tests/**, README.md
---
## Goal
One command configures GitHub so the squad can merge only into `development`, and only the PO (repo admin) can merge into `staging` and `main`.

## Acceptance criteria
- [x] `omi github` creates `staging` from `main` if missing.
- [x] Ruleset on `development`: no force push, no deletion only (the Coordinator pushes `.omi/` state directly; PR + CI there is enforced by the squad process).
- [x] Ruleset on `staging`/`main`: PR required, check `test`, updates restricted with bypass only for the repository admin role.
- [x] Re-running it updates the existing rulesets and creates no duplicates; it prints what changed.
- [x] If the token lacks admin, it stops with a clear message and changes nothing.
- [x] After applying, if the current user is a repo admin, it prints a warning: admins bypass the staging/main rule, so the squad account must be set back to Write.
- [x] Uses `gh api` via subprocess (no new dependencies); repo is taken from `gh repo view`.
- [x] A test covers the payload that gets built (no network).

## Checkpoint
Unblocked: PO is making the repo public (Free plan has no rulesets on private repos) and granting admin. Running `omi github` for real is the Coordinator's step after merge.
Done: all criteria implemented (omi github, rulesets() pure payload builder, test, README line).
Not done: real run against GitHub (Coordinator, after merge).
Tests: python tests/test_omi.py ok.
Next: merge, run omi github.
