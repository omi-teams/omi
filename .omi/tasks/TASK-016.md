---
id: TASK-016
title: Close minor review follow-ups in omi github --po and the worker scope check
status: done
depends: TASK-015
scope: src/omi/__init__.py, tests/**
---
## Goal
Close three small gaps reviewers noted in TASK-013/014/015. This is also the first live run of `omi worker`.

## Acceptance criteria
- [x] `omi github --po` checks repo visibility with the current (squad) account before `gh auth login`, so a private repo costs the PO no login.
- [x] After `--po` cleanup, if the active account is not the previous squad account, it prints a warning and exits non-zero.
- [x] The worker scope check also flags Windows 8.3 short names of git files (a component matching `GIT~<n>` or `GITATT~<n>`/`GITMOD~<n>`, case-insensitive).
- [x] Tests cover each case; `python tests/test_omi.py` passes.

## Checkpoint
Done: all 3 criteria (repo_info() pre-login visibility check; post-cleanup active-account warning+exit; 8.3 short-name flagging) + tests in test_github_po / test_worker.
Not done: -
Tests: all tests pass up to test_template_docker, which fails only because the container has no git; PurePosixPath.full_match (py3.13) is missing on py3.11 here, so I shimmed it for the run.
Next: Coordinator runs full suite on host.
