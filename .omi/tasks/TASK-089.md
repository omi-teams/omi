---
id: TASK-089
title: Clearer CLI feedback: Dockerfile diff hint, version check hint, hook result line
status: planned
depends: 
plan: PLAN-002
scope: src/omi/__init__.py, tests/test_omi.py
role: omi-agent-engineer
skills: []
refs: []
tool:
model:
effort:
step_settings:
workflow: omi-flow-feature
step:
---
## Goal
omi-board gaps #1, #2, #7, #8: when omi reports something, it says what happened and what to type next.

## Acceptance criteria
- [ ] When `docker/Dockerfile` differs from the template, `omi status` also prints one runnable command that shows the diff against the installed template file (e.g. `git diff --no-index <template path> docker/Dockerfile`) and says to merge by hand, since `omi init`/`upgrade` never overwrite it. Tested.
- [ ] `omi version` (and `--version`) prints the installed version plus a hint line `latest: python -m omi upgrade --check`; the `usage` text for `version` mentions it. Tested.
- [ ] `omi hook <event> <ID>` always prints a final line `hook <event> passed` or `hook <event> FAILED (exit N)`, also when the hook printed nothing. Tested.
- [ ] Regression test: `omi run` (write role) returns exit 6 when the post-run hook fails and the agent exited 0, and the engineer's `DONE` report does not change that. If the test shows the exit is already 6, no code change for this criterion.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next: start with `omi-task TASK-089`.
