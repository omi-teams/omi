---
id: PLAN-003
title: omi 0.3.2 - upgrade stamp gap and host-only review checks
status: active
---
## Goal
Fix the two gaps recorded in `.omi/decisions.md` on 2026-10-28 (reviewer UNVERIFIED vs Windows-host criteria; /omi-upgrade stopping while project files are behind the installed package), then release 0.3.2. PO decision 2026-10-28: 3 tasks, one fix each plus the bump.

## Done criteria
- TASK-093..095 are done and released as 0.3.2.
- omi-board upgrades to 0.3.2 with `/omi-upgrade`, and its `.omi/version` reads 0.3.2.
