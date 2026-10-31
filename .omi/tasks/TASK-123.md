---
id: TASK-123
title: Near-realtime omi board via a lightweight version endpoint
status: planned
depends: TASK-115, TASK-137
plan: PLAN-007
scope: src/omi/board/**, tests/test_board.py, tests/test_board_server.py, tests/test_board_web.py, .omi/tasks/TASK-123.md
role: omi-agent-engineer
skills: []
refs: []
tool:
model:
effort:
step_settings:
workflow: omi-flow-feature-ui
step:
---
## Goal
The omi board shows state changes within about 3 seconds: a cheap version endpoint tells the page when state changed, and only then does it reload the full data.

## Acceptance criteria
- [ ] `GET /api/version` (and per project `GET /api/projects/<name>/version`) returns the `origin/main` sha of GitHub omi-state after the shared fetch from TASK-137 (no file parsing); read-only, same CSP and path checks as the other endpoints.
- [ ] The page polls the version every 3 s while the tab is visible, and reloads the current view only when the hash changes; a failed version poll keeps the old view and shows the existing error/retry UI.
- [ ] The 30 s auto-refresh from TASK-115 is removed entirely: no countdown ("Làm mới sau N giây"), no auto-refresh toggle, no 30 s timer, and their CSS is deleted; the manual "Làm mới" button stays.
- [ ] Tests cover the version changing on a pushed state change, unchanged on no push, and the client reloading only on change; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
