---
id: TASK-114
title: omi board server and CLI
status: planned
depends: TASK-113
plan: PLAN-006
scope: src/omi/board/server.py, src/omi/cli.py, tests/test_omi.py, README.md
role: omi-agent-engineer
skills: []
refs: []
tool:
model:
effort:
step_settings:
workflow: omi-flow-feature-sensitive
step:
---
## Goal
`omi board [--port N] [--no-open]` serves the data layer as JSON and the static frontend on 127.0.0.1 only.

## Acceptance criteria
- [ ] Binds 127.0.0.1 (default port 8765), opens the browser unless `--no-open`, pulls state once at start like `omi status`, then serves `/api/projects`, `/api/projects/<name>`, `/api/projects/<name>/tasks/<id>` as JSON read fresh per request.
- [ ] Static files only from `board/web/`; `../`, encoded traversal, absolute paths and unknown routes return 404; only GET; no write to state or code repo.
- [ ] Responses set `Content-Type`, `X-Content-Type-Options: nosniff` and a CSP of `default-src 'self'`.
- [ ] Unit tests start the server on a free port against a temporary state and cover each route, traversal and method refusal; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
