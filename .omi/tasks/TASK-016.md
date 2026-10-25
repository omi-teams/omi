---
id: TASK-016
title: Close minor review follow-ups in omi github --po and the worker scope check
status: in-progress
depends: TASK-015
scope: src/omi/__init__.py, tests/**
---
## Goal
Close three small gaps reviewers noted in TASK-013/014/015. This is also the first live run of `omi worker`.

## Acceptance criteria
- [ ] `omi github --po` checks repo visibility with the current (squad) account before `gh auth login`, so a private repo costs the PO no login.
- [ ] After `--po` cleanup, if the active account is not the previous squad account, it prints a warning and exits non-zero.
- [ ] The worker scope check also flags Windows 8.3 short names of git files (a component matching `GIT~<n>` or `GITATT~<n>`/`GITMOD~<n>`, case-insensitive).
- [ ] Tests cover each case; `python tests/test_omi.py` passes.

## Checkpoint
Done:
Not done:
Tests:
Next:
