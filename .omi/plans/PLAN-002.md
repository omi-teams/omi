---
id: PLAN-002
title: omi 0.3.1 - gaps from the second omi-board session
status: active
---
## Goal
Fix the gaps the PO recorded in omi-board's second session (omi-board `docs/omi-squad-gaps/2026-10-27-session-52a026fd.md`), then release 0.3.1. PO decision 2026-10-28: 4 tasks; gap #9b (sidecar DB services in the worker) deferred; gaps #6 and #12b are fixed in omi-board itself (its `.omi/test.py`: stub `web/dist` in the container, drop the vet-only branch now that `/cache` is exec).

## Done criteria
- TASK-089..092 are done and released as 0.3.1.
- omi-board upgrades to 0.3.1 with `/omi-upgrade`.
