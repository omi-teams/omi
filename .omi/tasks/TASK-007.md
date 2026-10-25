---
id: TASK-007
title: Verify resume and Claude-to-Codex handover
status: done
depends: TASK-005
scope: docs/verification.md, src/omi/template/AGENTS.md, AGENTS.md
---
## Goal
Show that a task interrupted mid-way can be finished in a new session, on Claude Code or Codex, without redoing verified work.

## Acceptance criteria
- [x] Stop a task mid-way; a new Claude session resumes from the checkpoint and `omi status` drift, and only the remaining work gets redone.
- [x] Codex resumes the same kind of task using AGENTS.md and `codex exec` for the roles.
- [x] Any AGENTS.md fix needed for Codex is made; results are recorded in `docs/verification.md`.

## Checkpoint
Done: all checks PASS, see docs/verification.md (TASK-007).
Tests: n/a (docs and AGENTS.md only)
Next: none
