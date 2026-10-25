---
id: TASK-002
title: Ship prompt fixes found in the TASK-001 pilot
status: in-progress
depends: TASK-001
scope: src/omi/template/**, .claude/**, .gitattributes
---
## Goal
Land the fixes learned from running TASK-001, so the next task runs without the same friction.

## Acceptance criteria
- [ ] `engineer.md` (template + installed copy) says the agent's own task file is always writable.
- [ ] `omi-task` skill step 6 removes worktree/branch only if still present (`gh pr merge --delete-branch` already does it).
- [ ] `.gitattributes` with `* text=auto eol=lf` stops the LF/CRLF warnings.
- [ ] `python tests/test_omi.py` passes.

## Checkpoint
Done: the two prompt edits committed on `task/TASK-002` (engineer.md template + installed copy; omi-task step 6). `.gitattributes` with `* text=auto eol=lf` added.
Not done: nothing in scope.
Tests: `python tests/test_omi.py` exit 0.
Next: PO review and PR.
