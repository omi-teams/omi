---
id: TASK-099
title: State sync: auto pull/commit/push and omi sync
status: planned
depends: TASK-098
plan: PLAN-004
scope: src/omi/*.py, tests/test_omi.py, README.md
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
Several machines share one omi-state repo without the PO running git by hand.

## Acceptance criteria
- [ ] `omi status` in a detached project runs `git pull --rebase` on the state repo first (skipped with a one-line note when offline or no remote). Tested with a local bare remote.
- [ ] Every command that changes state (`step`, task start/done, decisions, plans, `omi run` reports/usage) commits only the files it changed in the state repo (`chore(<project>): <what>`) and pushes; a push failure prints `STATE NOT PUSHED: run omi sync` and keeps the commit. Tested.
- [ ] `omi sync` pulls, commits any leftover state change and pushes; a rebase conflict stops with the file list and changes nothing more. Tested.
- [ ] `omi sync` is listed in USAGE and pinned in `test_cli_characterization` (exit codes and key output).
- [ ] All tests pass on the Linux worker and the Windows host; in-repo mode behaviour is unchanged (existing tests untouched or only extended).

## Checkpoint
Done:
Not done:
Tests:
Next:
