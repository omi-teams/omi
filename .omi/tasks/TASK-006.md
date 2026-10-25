---
id: TASK-006
title: Spike Docker worker to block shell writes outside scope
status: planned
depends: TASK-004
scope: docker/**, docs/spikes/docker.md
---
## Goal
Find out whether a worker running Claude Code in a container on Windows, authenticated with the subscription, can be limited to writing only inside its worktree, including writes through shell.

## Acceptance criteria
- [ ] A Dockerfile plus a run script that mount the worktree read-write and nothing else writable from the project.
- [ ] Auth uses `claude setup-token` passed through an env var. The token never enters the image, git or logs.
- [ ] A shell write outside the worktree fails; a write inside succeeds.
- [ ] Avoid the known pitfalls from `../omi-squad` labs: CLI binaries on a `noexec` tmpfs fail with exit 126 (bake them into the image), and a Codex auth copy must keep `last_refresh`.
- [ ] `docs/spikes/docker.md` records the result, the cost (startup time, RAM) and a go/no-go recommendation.

## Checkpoint
Not done: needs a PO decision first. The spike uses subscription quota inside a container; check the terms of use for automated use.
Tests:
Next:
