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
Done: Dockerfile (node:24.11.0-trixie-slim, python3 3.13 + git), quiet docker build (log on failure), 8.3 regex git*~n, tests added
Not done: live omi worker --prove and in-container test run (no docker or py3.13 in this sandbox)

Tests: not runnable here (py3.11 lacks full_match)
Next: Coordinator runs live --prove and tests on host
Review round 1 (Coordinator, host): `python tests/test_omi.py` fails: tests/test_omi.py:323 in test_worker, `next(c[0] for c in calls if c[0][:2] == ["docker", "run"])` raises StopIteration (no `docker run` call recorded, likely the new quiet-build path in ensure_image changed the stubbed call sequence). This run uses the new image, so run the full suite in the container (`python3 tests/test_omi.py` with PYTHONPATH=src) and make it pass. Also reword engineer guidance only if in scope.

Round 2: fixed test_worker (calls cleared by later go(); build_fail now reset per go()). `PYTHONPATH=src python3 tests/test_omi.py` passes on py3.13.5 here. Live --prove still needs host docker.
