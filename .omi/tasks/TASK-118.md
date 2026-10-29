---
id: TASK-118
title: Split tests/test_omi.py into test files by area
status: in-progress
depends: TASK-107
plan: PLAN-005
scope: tests/**, .omi/tasks/TASK-118.md
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-refactor
step:
---
## Goal
The 5050-line `tests/test_omi.py` becomes several `tests/test_<area>.py` files (for example upgrade, install, attach/detached, init, github, worker, tasks, cli) with shared fakes in `tests/helpers.py`, so later tasks touch separate test files and can run in parallel. No product code changes.

## Acceptance criteria
- [ ] Each test file covers one area and stays under ~800 lines; shared fakes and fixtures (FakePopen, temp repos) live in `tests/helpers.py` and are imported, not copied.
- [ ] `python tests/test_omi.py` still runs every test and prints `ok` (CI and the post-run hook stay unchanged); each area file also runs on its own.
- [ ] The same 87 tests exist before and after, by name; no test body changes beyond imports and helper references.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:
