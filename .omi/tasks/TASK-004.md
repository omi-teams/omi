---
id: TASK-004
title: Verify hooks and agents live in a fresh Claude Code session
status: done
depends: TASK-002
scope: docs/verification.md
---
## Goal
Prove that what the unit test checks also holds inside real Claude Code: the session-start status, the scope guard and the named agents.

## Acceptance criteria
- [x] A new session shows `omi status` output without any tool call (SessionStart hook).
- [x] `/omi-status` prints status through `!` injection with no tool call.
- [x] `engineer`/`reviewer` show up as agent types and run with the model set in their frontmatter.
- [x] Edit/Write by an agent outside `scope` in a task worktree is blocked with the OMI message; inside scope it works.
- [x] Edit/Write to product code in the main checkout is blocked while a task worktree exists.
- [x] Results, including failures and the Claude Code version, are recorded in `docs/verification.md`.

## Checkpoint
Done: all checks PASS, see docs/verification.md.
Tests: n/a (docs only)
Next: none
