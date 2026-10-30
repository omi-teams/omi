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
step: security
---
## Goal
`omi board [--port N] [--no-open]` serves the data layer as JSON and the static frontend on 127.0.0.1 only.

## Acceptance criteria
- [ ] Binds 127.0.0.1 (default port 8765), opens the browser unless `--no-open`, pulls state once at start like `omi status`, then serves `/api/projects`, `/api/projects/<name>`, `/api/projects/<name>/tasks/<id>` as JSON read fresh per request.
- [ ] Static files only from `board/web/`; `../`, encoded traversal, absolute paths and unknown routes return 404; only GET; no write to state or code repo.
- [ ] Responses set `Content-Type`, `X-Content-Type-Options: nosniff` and a CSP of `default-src 'self'`.
- [ ] Unit tests start the server on a free port against a temporary state and cover each route, traversal and method refusal; all tests pass.

## Checkpoint
Security fix round 1 done: server.py Host check (403 via self.send in do_GET and refuse), cli.py `isascii() and isdigit()`, tests added (foreign Host, `²` port). `python3 tests/test_omi.py` ran in full and printed `ok`. Next: commit, step done + next (security round 2).
Review round 2 PASS. Security review round 1 FAIL:
- server.py: no `Host` header check, so DNS rebinding can read `/api/*` (verified: `Host: evil.example:80` gave 200). In `do_GET` and `refuse`, answer 403 through `self.send` (CSP/nosniff set) unless `Host` is exactly `127.0.0.1:<port>` or `localhost:<port>` (server's own port). Add a test: a foreign Host gets 403 on `/api/projects` and on a static path; the right Host gets 200.
- cli.py: `--port Â²` passes `isdigit()`, then `int()` raises a traceback. Validate with `port.isascii() and port.isdigit()`; add `Â²` to the bad-flag cases in `test_board_cli`.
Next: engineer fix round, commit, `omi step TASK-114 done` + `next` (review), then security review round 2.
Fix round 1 done and verified: cli.py catches OSError/OverflowError around make_server; server.py catches OSError/UnicodeError and answers via self.send; test_board_cli and test_unreadable_task added. `python3 tests/test_omi.py` ran in full and printed `ok`.
Next: commit, `omi step TASK-114 done` + `next`, then reviewer round 2.
Review round 1 PASS with findings, PO asked for one fix round:
- cli.py: catch OSError/OverflowError around make_server (port in use, >65535) and raise state.StateError("cannot bind 127.0.0.1:<port>: ...").
- server.py: also catch OSError and UnicodeError from data.*; answer via self.send (404 or 500) so CSP/nosniff are always set.
- tests: add a small test for `omi board` CLI flag validation, default port 8765, one-time pull and --no-open (patch pull, webbrowser and serve).
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
- build done 2026-10-30 09:25
- review started 2026-10-30 09:25
- review failed 2026-10-30 09:39
- build started 2026-10-30 09:39
- build done 2026-10-30 12:43
- review started 2026-10-30 12:43
- review done 2026-10-30 12:49
- security started 2026-10-30 12:49
- security failed 2026-10-30 12:56
- build started 2026-10-30 12:56
- build done 2026-10-30 13:07
- review started 2026-10-30 13:07
- review done 2026-10-30 13:16
- security started 2026-10-30 13:16

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
> NEEDS SCOPE: `tests/test_cli.py` â€” it pins the exact list of commands in `USAGE`, so I couldn't add the `omi board` usage line without breaking it. The command itself works and runs fine without that line.
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
2026-10-30 09:38 omi-agent-reviewer (claude):
> VERDICT: PASS
> - src/omi/app/cli.py:178-187 A port in use or above 65535 gives a raw traceback. I ran it: `--port 99999` raised `OverflowError`, and a second server on 8799 raised `OSError: Address already in use`. -> Catch `OSError` and `OverflowError` around `make_server` and raise `state.StateError("cannot bind 127.0.0.1:<port>: ...")`.
> - src/omi/board/server.py:270-275 Only `ValueError` and `FileNotFoundError` are caught. An unreadable or undecodable task file, which raises `OSError` or `UnicodeDecodeError`, produces a 500 with a stack trace on stderr and no CSP or nosniff headers. -> Also catch `OSError` and `UnicodeError`, and answer with a `self.send(...)` 404 or 500.
> - tests/test_board_server.py The `omi board` CLI path has no test: flag validation, the default port 8765, the one-time pull and `--no-open`. -> Add a small test for the argument validation.
> 
> AC: Binds 127.0.0.1 (default 8765), opens the browser unless `--no-open`, pulls once at start, serves the three JSON routes fresh per request âœ“ `make_server` binds `("127.0.0.1", port)`, and the test asserts that address. cli.py defaults to 8765, calls `state_sync.pull` once when the project is detached, and calls `webbrowser.open` only without `--no-open`; this part is from reading the code, with no test. The routes are tested, and `board.data` is uncached.
> AC: Static files only from `board/web/`; `../`, encoded traversal, absolute paths and unknown routes give 404; GET only; no writes âœ“ The test covers 18 bad paths, all 404, and POST/PUT/DELETE/PATCH/HEAD/OPTIONS all return 405 with `Allow: GET`. The handler never writes. `board/web/` does not exist yet, which the checkpoint says is deferred to a later task.
> [... truncated ...]
> Scope: every file in the diff is listed in the task's `scope`.
2026-10-30 12:38 omi-agent-engineer (claude):
> DONE
> - Fix round 1 was already in the worktree from the paused run, so I only verified it and changed no code. It has all three review fixes: `cli.py` turns a bind error into `StateError("cannot bind 127.0.0.1:<port>: ...")`, `server.py` answers `OSError` and `UnicodeError` through `self.send` with CSP and nosniff set, and `test_board_cli` and `test_unreadable_task` are new.
> - Files changed: `.omi/tasks/TASK-114.md` (checkpoint only). The code files are unchanged by this run (`src/omi/board/server.py`, `src/omi/app/cli.py`, `tests/test_board_server.py`).
> - Commit message: `feat(board): add omi board localhost server and CLI`
> - Tests: the full `python3 tests/test_omi.py` ran and printed `ok`. `tests/test_board_server.py` also ran on its own and passed.
> - Open issues: `board/web/` and the `pyproject.toml` package-data entry are left for the frontend task, so `/` returns 404 until then.
2026-10-30 12:42 hook post-run passed:
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
2026-10-30 12:49 omi-agent-reviewer (claude):
> VERDICT: PASS
> - src/omi/app/cli.py:298 `"Â²".isdigit()` is True but `int("Â²")` raises `ValueError`, so `--port Â²` gives a raw traceback instead of the usage error. This is minor. -> Validate with `port.isascii() and port.isdigit()`.
> - src/omi/app/cli.py:298 Ports above 65535 aren't rejected up front. They do reach the bind-error path and give a clean `StateError`, so behaviour is acceptable. No fix needed.
> 
> AC: Binds 127.0.0.1 (default 8765), opens the browser unless `--no-open`, pulls once, serves the three JSON routes fresh per request âœ“ `make_server` binds `("127.0.0.1", port)` and `test_server` asserts that address. `test_board_cli` now checks the default port 8765, one `pull` call, `webbrowser.open` called by default and not called with `--no-open`. The three routes return the expected JSON in `test_server`.
> AC: Static files only from `board/web/`; `../`, encoded traversal, absolute paths and unknown routes give 404; GET only; no writes âœ“ 18 bad paths all return 404 with `nosniff` set. POST, PUT, DELETE, PATCH, HEAD and OPTIONS return 405 with `Allow: GET`. The handler has no write path.
> AC: Responses set `Content-Type`, `X-Content-Type-Options: nosniff` and CSP `default-src 'self'` âœ“ Asserted on 200 and 404 responses. `test_unreadable_task` asserts the CSP header on a 500, and the 405 path sets the same headers.
> AC: Unit tests start the server on a free port against a temporary state and cover each route, traversal and method refusal; all tests pass âœ“ `python3 tests/test_omi.py` ran in full and printed `ok`. `python3 tests/test_board_server.py` also ran on its own and exited 0.
> 
> Scope: every changed file is listed in the task's `scope`. The round-1 fixes are present: the bind error becomes `StateError`, `OSError`/`UnicodeError` go through `self.send`, and `test_board_cli` and `test_unreadable_task` were added.
2026-10-30 12:56 omi-agent-security-reviewer (claude):
> VERDICT: FAIL
> - src/omi/board/server.py:371 The server never checks the `Host` header, so it is open to DNS rebinding. | why: a web page the user visits can rebind its hostname to 127.0.0.1 and read `/api/projects` and the task details, which include reports and checkpoints. Binding to 127.0.0.1 doesn't stop this. | verified: sent `GET /api/projects` with `Host: evil.example:80` and got 200 with a body. -> In `do_GET` and `refuse`, answer 403 or 404 through `self.send` unless `Host` is `127.0.0.1:<port>` or `localhost:<port>`. Add a test for it.
> - src/omi/app/cli.py:324 `--port Â²` passes `isdigit()`, but `int("Â²")` raises `ValueError`, so the user gets a traceback instead of the usage error. The round-2 reviewer flagged this and it is still unfixed. | why: `"Â²".isdigit()` is True. | verified: ran `'Â²'.isdigit()` and it printed `True`. I did not run `omi board --port Â²` itself. -> Check `port.isascii() and port.isdigit()`.
> 
> The background run finished with exit code 0. `python3 tests/test_omi.py` printed `ok` (the earlier unverified item is resolved). The two `omi board: http://127.0.0.1:8765/ ...` lines in the output come from `test_board_cli`.
2026-10-30 13:03 omi-agent-engineer (claude):
> DONE
> - Files changed: `src/omi/board/server.py`, `src/omi/app/cli.py`, `tests/test_board_server.py`, `.omi/tasks/TASK-114.md`.
> - Host check: `do_GET` and `refuse` now answer 403 through `self.send` (CSP and nosniff set) unless `Host` is exactly `127.0.0.1:<port>` or `localhost:<port>` for the server's own port.
> - Port check: `--port` now needs `isascii() and isdigit()`, so `--port ²` gives the usage error instead of a traceback.
> - Tests added: five foreign Host values get 403 on `/api/projects`, `/app.js` and a POST, and `localhost:<port>` gets 200. `²` is a new bad-flag case in `test_board_cli`.
> - Commit message: `fix(board): reject foreign Host header and non-ASCII port digits`
> - Tests: the full `python3 tests/test_omi.py` ran and printed `ok`, and `python3 tests/test_board_server.py` also passed on its own.
> - Open issues: none. `board/web/` and the `pyproject.toml` package-data entry are still left for the frontend task.
2026-10-30 13:07 hook post-run passed:
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
2026-10-30 13:16 omi-agent-reviewer (claude):
> ```
> VERDICT: PASS
> AC: Binds 127.0.0.1 (default 8765), opens browser unless --no-open, pulls once at start, serves the three JSON routes fresh per request ✓ cli.py:383-403 defaults to 8765, pulls once when detached, and calls webbrowser.open only without --no-open. server.py make_server binds ("127.0.0.1", port). test_board_cli checks the default port, one pull, and the open/--no-open behaviour. test_server checks the bind address and all three routes. board.data is read per request.
> AC: Static files only from board/web/; ../, encoded traversal, absolute paths and unknown routes give 404; GET only; no writes ✓ test_server sends 18 bad paths and gets 404 on each. POST, PUT, DELETE, PATCH, HEAD and OPTIONS return 405 with Allow: GET. server.py has a resolve()/is_relative_to confinement and no write path. A foreign Host header now gets 403, covered by test_server (five hosts, GET and POST).
> AC: Responses set Content-Type, X-Content-Type-Options: nosniff and CSP default-src 'self' ✓ send() sets all three. test_server asserts them on 200, 404 and 403 responses, and test_unreadable_task asserts the CSP on a 500. The 405 path sets nosniff and CSP in refuse().
> AC: Unit tests start the server on a free port (port 0) against a temporary state and cover each route, traversal and method refusal; all tests pass ✓ test_server, test_board_cli and test_unreadable_task are wired into tests/test_omi.py. The full `python3 tests/test_omi.py` exited 0 and printed `ok`. `tests/test_board_server.py` also ran on its own and exited 0.
> Scope: every changed file is in the task's scope. The last two security fixes (Host check, `isascii()` on the port) are present and tested.
> ```

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 12 | 5753 | 190869 | 92s | - | n/a |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 26 | 6501 | 411235 | 674s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 18 | 1757 | 215020 | 352s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 12 | 2822 | 203639 | 590s | - | PASS ed54d6d |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 16 | 1808 | 209280 | 367s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 10 | 1860 | 182917 | 247s | - | PASS a30e091 |
| omi-agent-security-reviewer | claude-sonnet-5-5 | medium | 6 | 582 | 100669 | 255s | 2/2 omi-skill-diff-security-review omi-skill-ci-workflow-audit | FAIL 48d69e0 |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 16 | 2853 | 253358 | 364s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 8 | 1606 | 164567 | 306s | - | PASS 8c8ea55 |
