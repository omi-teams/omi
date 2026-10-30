---
id: TASK-114
title: omi board server and CLI
status: in-progress
depends: TASK-113
plan: PLAN-006
scope: src/omi/board/server.py, src/omi/app/cli.py, tests/test_board_server.py, tests/test_omi.py, .omi/tasks/TASK-114.md
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature-sensitive
step: architect
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

## Steps
- plan started 2026-10-30 08:54
- plan done 2026-10-30 08:54
- architect started 2026-10-30 08:54

## Reports
2026-10-30 08:59 omi-agent-architect (claude):
> Server goes in `board/server.py` as a request handler only; `cli.py` handles flags, the one-time pull, opening the browser and the serve loop. One scope gap needs PO approval: `.omi/rules/omi-modules.md` doesn't list `board.server` yet.
> 
> ```
> RECOMMEND: A - put a thin handler with route allowlist in board/server.py (imports only board.data); cli.py does the args, one-time pull, browser and serve loop, so server tests need no patches or network. Scope gap for the PO: add .omi/rules/omi-modules.md (one line for board/server.py; layer order app.cli > board.server > board.data). TASK-097/100/113 already widened scope this way.
> OPTIONS: A: server = make_server(port, web=WEB) -> ThreadingHTTPServer + BaseHTTPRequestHandler; pull/webbrowser in cli / pro: small surface, testable on port 0 with a tmp web dir, server has no state.sync import; con: cli grows ~25 lines. B: server.serve(port, open) also owns pull and webbrowser / pro: cli is one line; con: server imports state.sync, tests must patch pull and webbrowser. C: SimpleHTTPRequestHandler(directory=web) / pro: less code; con: directory listings, 301 redirects, HEAD, its own translate_path and guessed types make "404 for traversal / GET only / fixed headers" hard to prove. Rejected.
> [... truncated ...]
> ```

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 12 | 5753 | 190869 | 92s | - | n/a |
