---
id: TASK-067
title: Claude agents use the current session's login (follow the session, like Codex)
status: in-progress
depends: TASK-065
scope: src/omi/__init__.py, tests/**, README.md
role: omi-agent-engineer
skills: [omi-skill-windows-powershell]
workflow: omi-flow-feature-sensitive
step:
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
Done:
Not done:
Tests:
Next:
Coordinator probe 2026-10-26: the session access token from ~/.claude/.credentials.json passed as CLAUDE_CODE_OAUTH_TOKEN into the worker image made `claude -p "Reply with exactly: PONG"` answer PONG (exit 0). The file has claudeAiOauth.{accessToken, expiresAt (ms), refreshToken, refreshTokenExpiresAt, scopes, subscriptionType, ...}. Architect step skipped: same pattern as TASK-065, proven by this probe.
