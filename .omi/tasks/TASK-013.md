---
id: TASK-013
title: Add omi github --po for a one-command PO run
status: done
depends: TASK-010
scope: src/omi/__init__.py, tests/**, README.md
---
## Goal
The PO applies rulesets with one command and no PO credential is left on the squad machine afterwards.

## Acceptance criteria
- [x] `omi github --po` records the active `gh` account, runs `gh auth login --web -h github.com` (the PO logs in in the browser), then applies the rulesets as the PO.
- [x] Afterwards, even when applying fails, it runs `gh auth logout -h github.com -u <po>` and `gh auth switch -h github.com -u <previous>`, then prints the active account.
- [x] If the account that logged in is the same as the previous (squad) account, it stops without logging out and says the PO must log in with their own account.
- [x] `omi github` without `--po` behaves as before.
- [x] A test covers the command sequence with `gh` stubbed (no network), including the failure path and the same-account guard.
- [x] README's `omi github` line mentions `--po`.

## Checkpoint
Done: all criteria (github --po, finally logout+switch, same-account guard, test, README)
Not done: -
Tests: python tests/test_omi.py ok
Next: review

- Fix round 1 (credential safety in github(po=True)): DONE. accounts() reads `gh auth status --json hosts` (local); login inside try/finally; cleanup logs out new accounts then switches to prev, both always attempted; leftover => warning + non-zero exit; empty prev aborts before login. tests/test_omi.py passes. Next: re-review.
