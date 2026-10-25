---
id: TASK-005
title: Show omi status drift between checkpoint and git
status: in-progress
depends: TASK-002
scope: src/omi/__init__.py, tests/**
---
## Goal
On resume, the Coordinator sees at once when a worktree has moved past its checkpoint, so it can verify instead of trusting stale notes.

## Acceptance criteria
- [ ] For each task worktree, `omi status` prints commits ahead of `development` and whether there are uncommitted changes.
- [ ] It warns `checkpoint stale` when commits exist after the last commit that touched the task file.
- [ ] The test covers both a clean case and a stale case.

## Checkpoint
Done: drift() line in omi status per worktree (ahead, uncommitted, checkpoint stale); test covers clean + stale.
Not done: nothing.
Tests: python tests/test_omi.py ok.
Next: review.
