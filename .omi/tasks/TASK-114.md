---
id: TASK-114
title: omi board server and CLI
status: in-progress
depends: TASK-113
plan: PLAN-006
scope: src/omi/board/server.py, src/omi/app/cli.py, tests/test_board_server.py, tests/test_omi.py, .omi/tasks/TASK-114.md, .omi/rules/omi-modules.md, tests/test_cli.py
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature-sensitive
step: build
---
## Goal
`omi board [--port N] [--no-open]` serves the data layer as JSON and the static frontend on 127.0.0.1 only.

## Acceptance criteria
- [ ] Binds 127.0.0.1 (default port 8765), opens the browser unless `--no-open`, pulls state once at start like `omi status`, then serves `/api/projects`, `/api/projects/<name>`, `/api/projects/<name>/tasks/<id>` as JSON read fresh per request.
- [ ] Static files only from `board/web/`; `../`, encoded traversal, absolute paths and unknown routes return 404; only GET; no write to state or code repo.
- [ ] Responses set `Content-Type`, `X-Content-Type-Options: nosniff` and a CSP of `default-src 'self'`.
- [ ] Unit tests start the server on a free port against a temporary state and cover each route, traversal and method refusal; all tests pass.

## Checkpoint
Done: board/server.py, `omi board` in cli.py, tests/test_board_server.py, test_omi.py wiring, omi-modules rule line + layer order.
Also done: USAGE line for `board` in cli.py, command list in tests/test_cli.py.
Not done: board/web/ frontend and pyproject package-data (later task).
Tests: full `python3 tests/test_omi.py` ran, printed `ok`.
Next: review and commit.

## Steps
- plan started 2026-10-30 08:54
- plan done 2026-10-30 08:54
- architect started 2026-10-30 08:54
- architect done 2026-10-30 08:59
- build started 2026-10-30 08:59

## Reports
2026-10-30 08:59 omi-agent-architect (claude):
> Server goes in `board/server.py` as a request handler only; `cli.py` handles flags, the one-time pull, opening the browser and the serve loop. One scope gap needs PO approval: `.omi/rules/omi-modules.md` doesn't list `board.server` yet.
> 
> ```
> RECOMMEND: A - put a thin handler with route allowlist in board/server.py (imports only board.data); cli.py does the args, one-time pull, browser and serve loop, so server tests need no patches or network. Scope gap for the PO: add .omi/rules/omi-modules.md (one line for board/server.py; layer order app.cli > board.server > board.data). TASK-097/100/113 already widened scope this way.
> OPTIONS: A: server = make_server(port, web=WEB) -> ThreadingHTTPServer + BaseHTTPRequestHandler; pull/webbrowser in cli / pro: small surface, testable on port 0 with a tmp web dir, server has no state.sync import; con: cli grows ~25 lines. B: server.serve(port, open) also owns pull and webbrowser / pro: cli is one line; con: server imports state.sync, tests must patch pull and webbrowser. C: SimpleHTTPRequestHandler(directory=web) / pro: less code; con: directory listings, 301 redirects, HEAD, its own translate_path and guessed types make "404 for traversal / GET only / fixed headers" hard to prove. Rejected.
> [... truncated ...]
> ```
2026-10-30 09:10 omi-agent-engineer (claude):
> NEEDS SCOPE: `tests/test_cli.py` — it pins the exact list of commands in `USAGE`, so I couldn't add the `omi board` usage line without breaking it. The command itself works and runs fine without that line.
> 
> - **Files changed:** `src/omi/board/server.py` (new), `src/omi/app/cli.py`, `tests/test_board_server.py` (new), `tests/test_omi.py`, `.omi/rules/omi-modules.md` (new `board/server.py` line, layer order `app.cli > board.server > board.data`), `.omi/tasks/TASK-114.md`.
> - **Behavior:** `omi board [--port N] [--no-open]` binds 127.0.0.1 only (default 8765), pulls state once if detached, opens the browser unless `--no-open`, and serves the three JSON routes. Traversal, unknown routes and absolute paths return 404; non-GET methods return 405; every response carries `X-Content-Type-Options` and the `default-src 'self'` CSP. The new test checks each of these against a temporary state on a free port.
> - **Tests:** `python3 tests/test_omi.py` ran in full and printed `ok`, including the new `test_board_server`. The browser-open and serve-loop path in `cli.py` has no test.
> - **Open issues:** To list `board` in `USAGE`, `tests/test_cli.py` needs to be in scope. `board/web/` doesn't exist yet, so `/` returns 404 until the frontend task adds it; that task also needs to add `pyproject.toml` package-data for `board/web`.
> - **Suggested commit:** `feat(board): add omi board localhost server and CLI`
2026-10-30 09:14 hook post-run passed:
> create AGENTS.md
> create docker/Dockerfile
> create docker/prove.sh
> create docker/proxy.py
> create .claude/settings.json
> create .claude/skills/omi-idea/SKILL.md
> create .claude/skills/omi-release/SKILL.md
> create .claude/skills/omi-status/SKILL.md
> create .claude/skills/omi-task/SKILL.md
> create .claude/skills/omi-upgrade/SKILL.md
> create .omi/agents/omi-agent-architect.md
> create .omi/agents/omi-agent-designer-ui.md
> create .omi/agents/omi-agent-devops.md
> create .omi/agents/omi-agent-docs-writer.md
> create .omi/agents/omi-agent-engineer.md
> create .omi/agents/omi-agent-qa-tester.md
> create .omi/agents/omi-agent-researcher.md
> create .omi/agents/omi-agent-reviewer.md
> create .omi/agents/omi-agent-security-reviewer.md
> create .omi/hooks/post-run.sh
> create .omi/plans/PLAN-000.md
> create .omi/references/nextjs-app-router.md
> create .omi/references/postgres-conventions.md
> create .omi/rules/docker.md
> create .omi/rules/go.md
> create .omi/rules/nextjs.md
> create .omi/rules/postgres.md
> create .omi/rules/python.md
> create .omi/skills/.gitkeep
> create .omi/skills/data/omi-skill-data-review/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-docker-worker-pitfalls/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-incident/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-release-checklist/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-rollback/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-windows-powershell/SKILL.md
> create .omi/skills/qa-web/omi-skill-web-qa/SKILL.md
> create .omi/skills/quality/omi-skill-ci-workflow-audit/SKILL.md
> create .omi/skills/quality/omi-skill-debug-root-cause/SKILL.md
> create .omi/skills/quality/omi-skill-diff-security-review/SKILL.md
> create .omi/skills/quality/omi-skill-simplify-review/SKILL.md
> create .omi/skills/quality/omi-skill-verify-evidence/SKILL.md
> create .omi/skills/ui/omi-skill-ui-a11y-review/SKILL.md
> create .omi/skills/ui/omi-skill-ui-direction/SKILL.md
> create .omi/skills/ui/omi-skill-ui-direction/references/style-presets.md
> [... truncated ...]
> ok
2026-10-30 09:21 omi-agent-engineer (claude):
> DONE
> - Files changed: `src/omi/board/server.py` (new), `src/omi/app/cli.py` (`omi board` command and USAGE line), `tests/test_board_server.py` (new), `tests/test_omi.py`, `tests/test_cli.py`, `.omi/rules/omi-modules.md`, `.omi/tasks/TASK-114.md`.
> - Commit message: `feat(board): add omi board localhost server and CLI`
> - Tests: the full `python3 tests/test_omi.py` ran and printed `ok`. That includes `test_board_server` (each route, traversal, method refusal, headers) and the updated USAGE command list in `test_cli.py`.
> - Open issues:
>   - The browser-open and serve-loop path in `cli.py` has no test.
>   - `board/web/` doesn't exist yet, so `/` returns 404 until the frontend task adds it. That task also needs `pyproject.toml` package-data for `board/web`.
2026-10-30 09:25 hook post-run passed:
> create AGENTS.md
> create docker/Dockerfile
> create docker/prove.sh
> create docker/proxy.py
> create .claude/settings.json
> create .claude/skills/omi-idea/SKILL.md
> create .claude/skills/omi-release/SKILL.md
> create .claude/skills/omi-status/SKILL.md
> create .claude/skills/omi-task/SKILL.md
> create .claude/skills/omi-upgrade/SKILL.md
> create .omi/agents/omi-agent-architect.md
> create .omi/agents/omi-agent-designer-ui.md
> create .omi/agents/omi-agent-devops.md
> create .omi/agents/omi-agent-docs-writer.md
> create .omi/agents/omi-agent-engineer.md
> create .omi/agents/omi-agent-qa-tester.md
> create .omi/agents/omi-agent-researcher.md
> create .omi/agents/omi-agent-reviewer.md
> create .omi/agents/omi-agent-security-reviewer.md
> create .omi/hooks/post-run.sh
> create .omi/plans/PLAN-000.md
> create .omi/references/nextjs-app-router.md
> create .omi/references/postgres-conventions.md
> create .omi/rules/docker.md
> create .omi/rules/go.md
> create .omi/rules/nextjs.md
> create .omi/rules/postgres.md
> create .omi/rules/python.md
> create .omi/skills/.gitkeep
> create .omi/skills/data/omi-skill-data-review/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-docker-worker-pitfalls/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-incident/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-release-checklist/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-rollback/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-windows-powershell/SKILL.md
> create .omi/skills/qa-web/omi-skill-web-qa/SKILL.md
> create .omi/skills/quality/omi-skill-ci-workflow-audit/SKILL.md
> create .omi/skills/quality/omi-skill-debug-root-cause/SKILL.md
> create .omi/skills/quality/omi-skill-diff-security-review/SKILL.md
> create .omi/skills/quality/omi-skill-simplify-review/SKILL.md
> create .omi/skills/quality/omi-skill-verify-evidence/SKILL.md
> create .omi/skills/ui/omi-skill-ui-a11y-review/SKILL.md
> create .omi/skills/ui/omi-skill-ui-direction/SKILL.md
> create .omi/skills/ui/omi-skill-ui-direction/references/style-presets.md
> [... truncated ...]
> ok

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 12 | 5753 | 190869 | 92s | - | n/a |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 26 | 6501 | 411235 | 674s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 18 | 1757 | 215020 | 352s | 1/1 omi-skill-lean-implementation | - |
