---
id: TASK-004
title: Verify hooks and agents live in a fresh Claude Code session
status: in-progress
depends: TASK-002
scope: docs/verification.md
---
## Goal
Prove that what the unit test checks also holds inside real Claude Code: the session-start status, the scope guard and the named agents.

## Acceptance criteria
- [ ] A new session shows `omi status` output without any tool call (SessionStart hook).
- [ ] `/omi-status` prints status through `!` injection with no tool call.
- [ ] `engineer`/`reviewer` show up as agent types and run with the model set in their frontmatter.
- [ ] Edit/Write by an agent outside `scope` in a task worktree is blocked with the OMI message; inside scope it works.
- [ ] Edit/Write to product code in the main checkout is blocked while a task worktree exists.
- [ ] Results, including failures and the Claude Code version, are recorded in `docs/verification.md`.

## Checkpoint
Not done: needs the PO to open a new Claude Code session in this repo, because hooks and agents created mid-session are not loaded.
Tests:
Next:
