---
id: TASK-086
title: Download caches live in the worktree so hooks and reviewers see the engineer's dependencies
status: in-progress
depends:
plan: PLAN-001
scope: src/omi/__init__.py, tests/test_omi.py, .gitignore, README.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: sonnet
effort: medium
workflow: omi-flow-feature
step:
---
## Goal
Gap #17 (omi-board session 97bfceb1): the post-run hook and read roles cannot use the dependencies the engineer downloaded (Go modules, npm, pip), because each container has its own `/cache` tmpfs (TASK-076) that disappears when the container stops. PO decision 2026-10-27: put the download caches inside the worktree at `/work/.omi-cache/` (gitignored); the engineer writes them, the hook and read roles read them through the existing read-only worktree mount. No new mounts or Docker volumes; the cache goes away with the worktree. Build caches (GOCACHE, XDG_CACHE_HOME) stay in the `/cache` tmpfs.

## Acceptance criteria
- [ ] Every omi container (write role, read roles, hooks) gets `GOMODCACHE=/work/.omi-cache/go-mod`, `npm_config_cache=/work/.omi-cache/npm`, `PIP_CACHE_DIR=/work/.omi-cache/pip` and `GOFLAGS=-modcacherw` (so Windows can delete the worktree); `GOCACHE` and `XDG_CACHE_HOME` stay under `/cache`. Tested on the docker argv for a write role, a read role and a hook.
- [ ] `.omi-cache/` is gitignored: `omi init` and `omi upgrade --apply` add it to `.gitignore` when missing (same helper style as `__pycache__/`); this repo's `.gitignore` has it. Files under `.omi-cache/` never count as out-of-scope changes. Tested.
- [ ] `git worktree remove` of a worktree holding a Go module cache works on the Windows host (Coordinator real check in a sandbox: write a read-only file tree under `.omi-cache/go-mod` as Go would without -modcacherw, and confirm -modcacherw files remove cleanly; or run `go mod download` in a worker if Go is in the image).
- [ ] README: one Vietnamese line on where download caches live and why.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next: start with `omi-task TASK-086` (PO chose Codex gpt-6.1-sol/medium; reviewer Claude sonnet/medium). After merge: omi-release 0.3.0, then real /omi-upgrade check on omi-board (PLAN-001 done criteria).
