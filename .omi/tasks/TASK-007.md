---
id: TASK-007
title: Verify resume and Claude-to-Codex handover
status: in-progress
depends: TASK-005
scope: docs/verification.md, src/omi/template/AGENTS.md, AGENTS.md
---
## Goal
Show that a task interrupted mid-way can be finished in a new session, on Claude Code or Codex, without redoing verified work.

## Acceptance criteria
- [ ] Stop a task mid-way; a new Claude session resumes from the checkpoint and `omi status` drift, and only the remaining work gets redone.
- [ ] Codex resumes the same kind of task using AGENTS.md and `codex exec` for the roles.
- [ ] Any AGENTS.md fix needed for Codex is made; results are recorded in `docs/verification.md`.

## Checkpoint
Done: Claude resume PASS; Codex resume PASS; AGENTS.md template fixed; results in docs/verification.md.
Not done: Codex end-to-end finish (sandbox blocks .git writes; needs PO run with full access). Root AGENTS.md synced.
Tests: no code changed; unittest result in report.
Next: PO reviews; optionally rerun Codex with full access.
