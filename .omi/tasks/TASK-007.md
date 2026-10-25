---
id: TASK-007
title: Verify resume and Claude-to-Codex handover
status: planned
depends: TASK-005
scope: docs/verification.md, src/omi/template/AGENTS.md
---
## Goal
Show that a task interrupted mid-way can be finished in a new session, on Claude Code or Codex, without redoing verified work.

## Acceptance criteria
- [ ] Stop a task mid-way; a new Claude session resumes from the checkpoint and `omi status` drift, and only the remaining work gets redone.
- [ ] Codex resumes the same kind of task using AGENTS.md and `codex exec` for the roles.
- [ ] Any AGENTS.md fix needed for Codex is made; results are recorded in `docs/verification.md`.

## Checkpoint
Not done: Codex is not installed. The PO installs it and logs in with their subscription.
Tests:
Next:
