---
id: TASK-138
title: Harden session volumes and board fetch; step back to architect
status: planned
depends:
plan: PLAN-007
scope: src/omi/worker/session.py, src/omi/worker/docker.py, src/omi/worker/run.py, src/omi/board/source.py, src/omi/project/tasks.py, tests/test_worker.py, tests/test_board.py, tests/test_tasks.py, .omi/tasks/TASK-138.md
role: omi-agent-engineer
skills: []
refs: []
tool:
model:
effort:
step_settings:
workflow: omi-flow-feature-sensitive
step:
---
## Goal
Close the known issues left by TASK-120 and TASK-137, and let the Coordinator send a task back to its architect step.

## Acceptance criteria
- [ ] A refused `docker volume rm` makes the next `--fresh` or fallback run abort (or use a new volume name) instead of reusing the old volume. Tested.
- [ ] Session volume names and the `omi-repo` label include a short hash of the main checkout path, so two repos with the same folder name never share volumes or have them cleaned. Tested.
- [ ] Ctrl-C or a timeout during the token scan still drops the volume (scan container killed by name). Tested.
- [ ] The board's `git fetch` runs with `GIT_TERMINAL_PROMPT=0` and a timeout; a timeout serves the last snapshot with `stale: true`. Tested.
- [ ] `omi step <ID> back --to <step> --why <reason>` returns a task to an earlier write step (e.g. architect) and logs it; tested.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next: from TASK-120 (PR #128) and TASK-137 (PR #127) Known issues, and the TASK-120 re-plan that had no `omi step` path back to architect.
