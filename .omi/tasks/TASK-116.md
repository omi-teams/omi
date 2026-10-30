---
id: TASK-116
title: Pilot omi board on real state
status: in-progress
depends: TASK-115
plan: PLAN-006
scope: docs/pilot-board.md, README.md
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature
step:
---
## Goal
Prove the spec's success criteria 1-4 on the pilot omi-state and document how to use the board.

## Acceptance criteria
- [ ] `docs/pilot-board.md` (Vietnamese) lists criteria 1-4 with the command or action and its result on the pilot state (omi-pilot-splitbill, TASK-003), on the Windows host and Linux.
- [ ] README documents `omi board` in at most 8 lines.
- [ ] Gaps found are listed for a later plan.

## Checkpoint
Host evidence (Coordinator, Windows 11 host, 2026-10-30, omi at development 478f894). The worker cannot read the real omi-state, so write the doc from these lines and do not re-run them:
- C1: `omi board` (port 8801) on the real `~/.omi/state` -> `/api/projects/omi-pilot-splitbill` returns plan PLAN-000 and kanban done=[TASK-003]. `/api/projects/omi-pilot-splitbill/tasks/TASK-003`: Steps and Reports text equal the file sections (compared byte for byte), and Usage has 2 rows, the same as the file (engineer + reviewer PASS 98f8665).
- C2: a copy of the state with `OMI_STATE=<copy>` (port 8802): editing TASK-003 `title:` -> the next API request returns the new title without restarting the server.
- C3: `title: <script>alert(1)</script>` comes back as plain JSON text, and the UI inserts text with textContent only (TASK-115 static test). The paths `/../../etc/passwd`, `/%2e%2e/%2e%2e/README.md`, `/api/projects/..%2f..%2f/tasks/x` and `/api/projects/omi-pilot-splitbill/tasks/..%2fTASK-003` (`curl --path-as-is`) all return 404. The CSP header is `default-src 'self'`.
- C4: Windows host: C1-C3 above, and `python tests/test_omi.py` -> ok (only the Playwright browser test is skipped). Linux: CI `ubuntu-latest` on development 478f894 -> success, and the Docker worker (Linux) runs `tests/test_omi.py` -> ok in every TASK-115/134 run. Browser QA in real Chrome at 360/390/768/1280 px is recorded in TASK-115.
- Gaps seen: no Playwright on the host or the worker (TASK-128); the board shows only the projects in the registry (the omi repo itself is not listed); a done task shows its last step as current, and Usage scrolls inside its card (TASK-125).
Done:
Not done:
Tests:
Next:
