---
id: TASK-006
title: Spike Docker worker to block shell writes outside scope
status: done
depends: TASK-004
scope: docker/**, docs/spikes/docker.md
---
## Goal
Find out whether a worker running Claude Code in a container on Windows, authenticated with the subscription, can be limited to writing only inside its worktree, including writes through shell.

## Acceptance criteria
- [x] A Dockerfile plus a run script that mount the worktree read-write and nothing else writable from the project.
- [x] Auth uses `claude setup-token` passed through an env var. The token never enters the image, git or logs.
- [x] A shell write outside the worktree fails; a write inside succeeds.
- [x] Avoid the known pitfalls from `../omi-squad` labs: CLI binaries on a `noexec` tmpfs fail with exit 126 (bake them into the image), and a Codex auth copy must keep `last_refresh`.
- [x] `docs/spikes/docker.md` records the result, the cost (startup time, RAM) and a go/no-go recommendation.

## Checkpoint
Done: spike complete, recommendation go (see docs/spikes/docker.md); live claude check passed with the PO token.
Not done: terms-of-use check, RAM under a real task, wiring the container into omi-task (a future task).
Tests: docker/prove.sh all PASS; live check PASS.
Next: none
