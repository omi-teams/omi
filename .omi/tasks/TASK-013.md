---
id: TASK-013
title: Add omi github --po for a one-command PO run
status: in-progress
depends: TASK-010
scope: src/omi/__init__.py, tests/**, README.md
---
## Goal
The PO applies rulesets with one command and no PO credential is left on the squad machine afterwards.

## Acceptance criteria
- [ ] `omi github --po` records the active `gh` account, runs `gh auth login --web -h github.com` (the PO logs in in the browser), then applies the rulesets as the PO.
- [ ] Afterwards, even when applying fails, it runs `gh auth logout -h github.com -u <po>` and `gh auth switch -h github.com -u <previous>`, then prints the active account.
- [ ] If the account that logged in is the same as the previous (squad) account, it stops without logging out and says the PO must log in with their own account.
- [ ] `omi github` without `--po` behaves as before.
- [ ] A test covers the command sequence with `gh` stubbed (no network), including the failure path and the same-account guard.
- [ ] README's `omi github` line mentions `--po`.

## Checkpoint
Done:
Not done:
Tests:
Next:
