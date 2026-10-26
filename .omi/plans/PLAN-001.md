---
id: PLAN-001
title: omi 0.3.0 - gaps from the first omi-board session, and omi upgrade
status: active
---
## Goal
Fix the gaps the PO recorded in omi-board's first real session (omi-board `docs/omi-squad-gaps/2026-10-26-session-97bfceb1.md`) and add `omi upgrade`, then release 0.3.0. PO model plan (2026-10-26): TASK-080 (Claude) and TASK-081 (Codex) research the models and efforts each session supports; TASK-082 puts concrete model/effort choices into the agent catalog and config (gap #1), so no run is `codex-default`/`none`, and every task-start question offers Claude Code vs Codex. Gap #9 (tool per step) is revisited after TASK-082.

## Done criteria
- TASK-076..082 are done and released as 0.3.0.
- omi-board upgrades itself with `/omi-upgrade` (real check).
