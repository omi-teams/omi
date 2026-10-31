---
id: TASK-137
title: omi board reads GitHub omi-state as its only source
status: in-progress
depends: TASK-115
plan: PLAN-007
scope: src/omi/board/**, tests/test_board.py, tests/test_board_server.py, tests/test_board_web.py, .omi/tasks/TASK-137.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature
step:
---
## Goal
Every board refresh shows exactly what is on `origin/main` of the GitHub omi-state repo; the local clone is only a read-only cache and its path is never shown.

## Acceptance criteria
- [ ] Before each API read the board runs `git fetch` on the state repo (at most once per 10 s, shared by concurrent requests) and reads files from `origin/main` (e.g. `git show`/`ls-tree` or a read-only worktree), never from uncommitted or unpushed local files; it never pulls, commits, pushes or changes the local working tree.
- [ ] Each response carries `source: {"repo": "<origin URL without credentials>", "sha": "<origin/main sha>", "fetched_at": "<time>", "stale": false}`; when fetch fails it serves the last fetched `origin/main` with `stale: true` and the page shows "Dữ liệu cũ - không kết nối được GitHub (lúc <giờ>)".
- [ ] No local filesystem path appears in any API response or page; the header shows "github.com/omi-teams/omi-state @ <sha7>".
- [ ] Tests with a local bare repo as origin cover: a pushed change appears, a local unpushed change does not, fetch failure gives `stale: true`, and no response contains the state dir path; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
