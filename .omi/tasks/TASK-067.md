---
id: TASK-067
title: Claude agents use the current session's login (follow the session, like Codex)
status: done
depends: TASK-065
scope: src/omi/__init__.py, tests/**, README.md
role: omi-agent-engineer
skills: [omi-skill-windows-powershell]
workflow: omi-flow-feature-sensitive
step: accept
---
## Goal
The PO uses several Claude accounts. Worker agents used the token stored by `omi token set` (made with `claude setup-token` under whatever account was logged in then), not the account of the current Claude Code session. Make agents follow the session, as Codex follows the host ChatGPT login (TASK-065).

## Acceptance criteria
- [x] Claude secret order: env `CLAUDE_CODE_OAUTH_TOKEN` (explicit override), then the session login `claudeAiOauth.accessToken` read at run time from `~/.claude/.credentials.json` (or `$CLAUDE_CONFIG_DIR/.credentials.json`), then the stored token (`omi token set`). Only the access token is passed (by name, as today); the refresh token never leaves the host; omi never stores or logs the session token.
- [x] An expired session token (`expiresAt` in ms is past) is skipped with a note `session login expired: use Claude Code once to refresh` and falls through to the stored token; if nothing is usable, the existing no-token message also names this option.
- [x] `omi run` prints which source it used (`claude auth: env|session|stored`), never the value; `omi status` unaffected; Codex path unchanged.
- [x] Tests for the order, expiry, missing file, and no token value in argv; `python tests/test_omi.py` passes.
- [x] Coordinator proves it with one real run (session token, `claude auth: session`), and README "Lấy và lưu key" says agents follow the Claude Code login by default.

## Checkpoint
Done: claude_secret() (env, session, stored), run prints `claude auth: <source>`, expiry note, no-token message, tests, README.
Not done: real run proof (Coordinator).
Tests: python3 tests/test_omi.py ok.
Round 2 done: (1) run_role calls claude_auth() once for claude (no second read); (2) claude_auth() prints the expiry note and `claude auth: <source>`, also after a codex->claude quota switch; (3) test_review_round_flow runs a session-login run and asserts `claude auth: session` with no token or refresh value in output. python3 tests/test_omi.py exit 0.
Next: Coordinator real run.
Coordinator probe 2026-10-26: the session access token from ~/.claude/.credentials.json passed as CLAUDE_CODE_OAUTH_TOKEN into the worker image made `claude -p "Reply with exactly: PONG"` answer PONG (exit 0). The file has claudeAiOauth.{accessToken, expiresAt (ms), refreshToken, refreshTokenExpiresAt, scopes, subscriptionType, ...}. Architect step skipped: same pattern as TASK-065, proven by this probe.

Coordinator real run 2026-10-26: `omi run omi-agent-reviewer TASK-067` with this worktree's code printed `claude auth: session` and the reviewer ran (VERDICT PASS) on the session account.
Round 2 (review notes): (1) run_role: call claude_secret() once for claude (no second read via tool_secret). (2) After a codex->claude quota switch, print the `claude auth: <source>` line (and the expiry note) too. (3) Add a run-level test asserting `claude auth: session` with a temp CLAUDE_CONFIG_DIR.
## Steps
- plan started 2026-10-26 11:49
- plan done 2026-10-26 11:49
- architect started 2026-10-26 11:49
- architect skipped 2026-10-26 11:49: same pattern as TASK-065, proven by the Coordinator probe in the Checkpoint
- build started 2026-10-26 11:49
- build done 2026-10-26 11:50
- review started 2026-10-26 11:50
- review done 2026-10-26 11:53
- security started 2026-10-26 11:53
- security done 2026-10-26 13:01
- accept started 2026-10-26 13:01
PO approval accept: "Chấp nhận, merge" (session token scopes broader than setup-token accepted: egress api.anthropic.com only, token lives hours)
- accept done 2026-10-26 13:01

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
2026-10-26 11:51 omi-agent-reviewer (claude):
> VERDICT: PASS
> - src/omi/__init__.py:1633 `run_role` calls `tool_secret(tool)` and then `claude_secret()` again for claude. The credentials file is read twice and the first result is thrown away. -> Call `claude_secret()` once, and only fall back to `tool_secret` for codex.
> - src/omi/__init__.py:1755 When codex hits its usage limit and the run switches to claude, `claude auth: <source>` and the expiry note are not printed. The AC says `omi run` prints which source it used. -> After the switch, print the source line when `other == "claude"`.
> - tests/test_omi.py:1652 No test drives `run_role` with a session credential, so `claude auth: session` is never checked in the output. Only the `env` case is asserted, at line 1466. -> Add a run-level assertion for `session`. The Coordinator's real-run proof should also cover it.
> 
> AC: Secret order env → session → stored; only the access token is read; the refresh token stays on the host ✓ `claude_secret()` at src/omi/__init__.py:960-976 follows that order. It reads only `accessToken` and `expiresAt`. The token goes into the container by env name via `worker_argv(env_names=(TOKEN_ENV,))`. `test_claude_session_login` covers env > session > stored and that `REAL-REFRESH` is never returned. Nothing writes or logs the session value.
> AC: Expired session is skipped with the note and falls through to stored; the no-token message names the option ✓ The note text is exact. The test covers both expired → stored and expired with nothing stored, where the value is None and the note is kept. The no-token `sys.exit` message includes the Claude Code login and the note.
> [... truncated ...]
> AC: Real run proof and README note ◐ The README "Lấy và lưu key" now says agents follow the Claude Code login by default. The real-run proof (`claude auth: session`) is still open and is the Coordinator's job.
2026-10-26 11:52 omi-agent-engineer (claude):
> DONE
> 
> Files changed: `src/omi/__init__.py`, `tests/test_omi.py`, `.omi/tasks/TASK-067.md` (Checkpoint).
> 
> Round 2 review notes, all addressed:
> 1. `run_role` now reads the Claude secret once via a new `claude_auth()` helper. The codex path still uses `tool_secret`.
> 2. `claude_auth()` prints the expiry note and `claude auth: <source>`. It is also used after a codex→claude quota switch, so that path prints the line too.
> 3. `test_review_round_flow` runs a session-login case with a temp `CLAUDE_CONFIG_DIR`. It asserts `claude auth: session` and that neither the access nor the refresh token appears in the output.
> 
> Test: `python3 tests/test_omi.py` exits 0.
> 
> Suggested commit: `feat(run): claude agents follow the current Claude Code session login`
> 
> Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>
> 
> Open: the Coordinator's real run (`claude auth: session`) is still needed. I did not touch the README in this round.
2026-10-26 11:53 omi-agent-reviewer (claude):
> VERDICT: PASS
> - `tests/test_omi.py:1660` The AC asks for a test that no token value appears in argv. The new tests only check that stdout has no token, and argv relies on an older by-name test. This is a gap, not a defect. -> Optionally assert on the captured argv in the session-login run in `test_review_round_flow`.
> - `.omi/tasks/TASK-067.md` The diff edits the task file, which is outside the declared `scope`. This is normally harness bookkeeping. -> No action unless scope is enforced strictly.
> 
> AC: Secret order env → session → stored; only the access token is passed, by name; the refresh token stays on the host ✓ `claude_secret()` (`src/omi/__init__.py:960`) checks env first, then `claudeAiOauth.accessToken` from `$CLAUDE_CONFIG_DIR` or `~/.claude`, then the stored token. It reads only `accessToken` and `expiresAt`. `test_claude_session_login` asserts the order and that `REAL-REFRESH` is never returned.
> AC: An expired session is skipped with the note and falls through to stored; the no-token message names this option ✓ `expiresAt` is compared in ms. The test covers expired → stored, and expired with nothing stored, where the value is None and the note is kept. The `sys.exit` message includes the Claude Code login and the note.
> AC: `omi run` prints `claude auth: env|session|stored`, never the value; `omi status` and Codex are unaffected ✓ `claude_auth()` prints the source line and the expiry note. `run_role` calls it once, and the codex→claude quota-switch path calls it too. `test_review_round_flow` asserts `claude auth: env` and `claude auth: session`, and that `sess-tok` and `REAL-REFRESH` are absent from the output. `tool_secret` for codex is unchanged.
> [... truncated ...]
> AC: The Coordinator's real run and the README note ✓ The README "Lấy và lưu key" now says agents follow the Claude Code login by default and lists the order. The task file records the real run printing `claude auth: session`. I didn't re-run it here.
2026-10-26 11:54 omi-agent-security-reviewer (claude):
> ```
> VERDICT: PASS
> - No blocking issues. I traced the token flow: `claude_secret()` (src/omi/__init__.py:960) reads only `accessToken` and `expiresAt` and never reads the refresh token. `attempt()` (1676-1679) puts the value in the child environment, and `worker_argv` passes only `-e NAME`, so the value never appears in argv. `claude_auth()` (981) and the no-token exit (1649) print only the source name and the expiry note. `python3 tests/test_omi.py` exited 0.
> - src/omi/__init__.py:222 On Windows the env token now overrides the stored token; before, the stored token won. | why: this changes what Windows users get | verified: code read; old `token()` at 923 checked the stored token first -> matches the AC ("explicit override"), so no fix needed; just be aware of it.
> UNVERIFIED: The session OAuth token probably has broader scopes than a `setup-token` token (which covers inference only), and it is now exposed to the worker agent's environment. To confirm, compare the `scopes` field in `.credentials.json` with a setup-token's scopes and check that the worker's egress allowlist only allows Anthropic API hosts.
> UNVERIFIED: A session token that expires in a few minutes is still accepted, so a long run could fail partway through. To confirm, start a run with `expiresAt` set to now + 60s.
> ```

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 20 | 5879 | 287406 | 77s | 2/2 omi-skill-windows-powershell omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 8 | 2052 | 95998 | 30s | - | PASS be878b3 |
| omi-agent-engineer | claude-haiku-5-5 | low | 18 | 4985 | 242737 | 59s | 1/1 omi-skill-windows-powershell | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 4 | 1599 | 45167 | 25s | - | PASS 27b1a83 |
| omi-agent-security-reviewer | claude-opus-5-5 | high | 12 | 2537 | 175990 | 41s | 2/2 omi-skill-diff-security-review omi-skill-ci-workflow-audit | PASS 7827340 |
