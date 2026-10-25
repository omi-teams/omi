---
id: TASK-017
title: Make the worker image able to run this project's tests
status: in-progress
depends: TASK-016
scope: src/omi/template/docker/**, src/omi/__init__.py, tests/**
---
## Goal
The first live `omi worker` run (TASK-016) could not run the tests in the container: Python 3.11 lacks `PurePosixPath.full_match` and `git` is missing.

## Acceptance criteria
- [ ] The default image has Python >= 3.13 and `git`, still pinned (base image tag, claude-code version).
- [ ] `git` in the container cannot reach the host repo: `.git` stays a read-only bind, and the engineer prompt still says it must not commit.
- [ ] `omi worker` prints the `docker build` log only when the build fails; on success it prints just the engineer's report.
- [ ] The 8.3 short-name check covers any `.git*` name (`GIT*~<n>`), not only GIT/GITATT/GITMOD.
- [ ] A live `omi worker --prove` and `python tests/test_omi.py` inside the container both pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
