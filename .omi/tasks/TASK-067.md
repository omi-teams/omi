---
id: TASK-067
title: Claude agents use the current session's login (follow the session, like Codex)
status: in-progress
depends: TASK-065
scope: src/omi/__init__.py, tests/**, README.md
role: omi-agent-engineer
skills: [omi-skill-windows-powershell]
workflow: omi-flow-feature-sensitive
step: build
---
## Goal
The PO uses several Claude accounts. Worker agents used the token stored by `omi token set` (made with `claude setup-token` under whatever account was logged in then), not the account of the current Claude Code session. Make agents follow the session, as Codex follows the host ChatGPT login (TASK-065).

## Acceptance criteria
- [ ] Claude secret order: env `CLAUDE_CODE_OAUTH_TOKEN` (explicit override), then the session login `claudeAiOauth.accessToken` read at run time from `~/.claude/.credentials.json` (or `$CLAUDE_CONFIG_DIR/.credentials.json`), then the stored token (`omi token set`). Only the access token is passed (by name, as today); the refresh token never leaves the host; omi never stores or logs the session token.
- [ ] An expired session token (`expiresAt` in ms is past) is skipped with a note `session login expired: use Claude Code once to refresh` and falls through to the stored token; if nothing is usable, the existing no-token message also names this option.
- [ ] `omi run` prints which source it used (`claude auth: env|session|stored`), never the value; `omi status` unaffected; Codex path unchanged.
- [ ] Tests for the order, expiry, missing file, and no token value in argv; `python tests/test_omi.py` passes.
- [ ] Coordinator proves it with one real run (session token, `claude auth: session`), and README "Lấy và lưu key" says agents follow the Claude Code login by default.

## Checkpoint
Done: claude_secret() (env, session, stored), run prints `claude auth: <source>`, expiry note, no-token message, tests, README.
Not done: real run proof (Coordinator).
Tests: python3 tests/test_omi.py ok.
Next: Coordinator real run.
Coordinator probe 2026-10-26: the session access token from ~/.claude/.credentials.json passed as CLAUDE_CODE_OAUTH_TOKEN into the worker image made `claude -p "Reply with exactly: PONG"` answer PONG (exit 0). The file has claudeAiOauth.{accessToken, expiresAt (ms), refreshToken, refreshTokenExpiresAt, scopes, subscriptionType, ...}. Architect step skipped: same pattern as TASK-065, proven by this probe.

## Steps
- plan started 2026-10-26 11:49
- plan done 2026-10-26 11:49
- architect started 2026-10-26 11:49
- architect skipped 2026-10-26 11:49: same pattern as TASK-065, proven by the Coordinator probe in the Checkpoint
- build started 2026-10-26 11:49

## Reports
2026-10-26 11:50 omi-agent-engineer (claude):
> DONE (the real-run proof is left to the Coordinator)
> - Files changed: `src/omi/__init__.py`, `tests/test_omi.py`, `README.md`, `.omi/tasks/TASK-067.md` (Checkpoint).
> - New `claude_secret()` uses `CLAUDE_CODE_OAUTH_TOKEN` first, then the session `accessToken` from `~/.claude/.credentials.json` (or `$CLAUDE_CONFIG_DIR`), then the stored token. It only reads the access token.
> - An expired session (`expiresAt` in ms is past) is skipped with the note `session login expired: use Claude Code once to refresh`, and it falls through to the stored token. The no-token message now also names the Claude Code login and the expiry note.
> - `omi run` prints `claude auth: env|session|stored`. That line now comes before the `tool:` line, so I updated the one test assertion that checked the output. The Codex path is unchanged, and the token still travels by env name only.
> - New `test_claude_session_login` covers the order, expiry, missing file, and the refresh token not being returned. No token value in argv is covered by the existing by-name test at `tests/test_omi.py` line 460. `tests/test_omi.py` now sets `CLAUDE_CONFIG_DIR` to a temp dir, so the host's real login isn't picked up. `python3 tests/test_omi.py` passes.
> - README "Lấy và lưu key" now says agents follow the Claude Code login by default.
> - Suggested commit: `feat(run): claude agents follow the current Claude Code session login`
> - Open: the real run that shows `claude auth: session`, as the task asks for.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 20 | 5879 | 287406 | 77s | 2/2 omi-skill-windows-powershell omi-skill-lean-implementation | - |
