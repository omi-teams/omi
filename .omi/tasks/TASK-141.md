---
id: TASK-141
title: Per-task omi clean that never kills another running task
status: planned
depends: TASK-138
plan:
scope: src/omi/worker/docker.py, src/omi/worker/session.py, src/omi/app/cli.py, src/omi/template/dot-claude/skills/omi-task/SKILL.md, src/omi/template/AGENTS.md, src/omi/template_shas.json, .claude/skills/omi-task/SKILL.md, AGENTS.md, tests/test_worker.py, tests/test_cli.py, .omi/tasks/TASK-141.md
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
Cleaning up after one task never stops another task's run. On 2026-10-31 the post-merge `omi clean` for TASK-136 removed every omi container of the repo and killed TASK-121's running reviewer (exit 137).

## Acceptance criteria
- [ ] `omi clean <ID>` removes only containers and session volumes labelled `omi-task=<ID>` for this repo (no networks, no images) and prints the same summary line. Tested with a fake `docker` that lists containers of two tasks.
- [ ] Bare `omi clean` (and `--all`) refuses with `RUNNING: <ID> <role>, ...; use omi clean <ID>, or --force` and a non-zero exit while any omi container of this repo is running; `--force` keeps today's behaviour. Stopped containers do not block. Tested.
- [ ] omi-task skill step 7 (template and repo copy) runs `omi clean <ID>` after each merge and the full `omi clean` / `omi clean --all` only when no other task is in progress; AGENTS.md template copy matches if it mentions clean; `template_shas.json` updated.
- [ ] All tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next: containers already carry `omi-task` (docker.py `run_labels`); session volumes carry `omi-task` (session.py). TASK-138 changes volume names and the `omi-repo` label: build on its result.
