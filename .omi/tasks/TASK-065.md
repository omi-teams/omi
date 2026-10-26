---
id: TASK-065
title: Run Codex in the worker with the PO's ChatGPT login (no API key)
status: in-progress
depends: TASK-054
scope: src/omi/__init__.py, src/omi/template/docker/**, tests/**, README.md
role: omi-agent-engineer
skills: [omi-skill-docker-worker-pitfalls, omi-skill-windows-powershell]
workflow: omi-flow-feature-sensitive
step: security
---
## Goal
The PO has a ChatGPT subscription and the host Codex CLI is "Logged in using ChatGPT" (~/.codex/auth.json, auth_mode chatgpt). Let `omi run --tool codex` use it without an OpenAI API key: pass only the short-lived access token, never the refresh token.

## Acceptance criteria
- [ ] Codex secret order: stored API key (`omi token set --tool codex`), then env `OPENAI_API_KEY`, then the host ChatGPT login: `tokens.access_token` read from `~/.codex/auth.json` (or `$CODEX_HOME/auth.json`) at run time, never stored by omi, never logged.
- [ ] ChatGPT mode passes the token by name only (e.g. `-e OMI_CODEX_AUTH`), and the container writes a slim `~/.codex/auth.json` from that env into its tmpfs home before `codex exec`; the real refresh token never enters the container. Allowlist covers the hosts Codex needs in this mode (find them with a real run; e.g. chatgpt.com), added per tool in code.
- [ ] Expired or missing login gives a clear message: run `codex` once on the host (or `codex login`) and retry. No API-key path or Claude path change; tests for the secret order, argv (no token value) and the missing/expired cases.
- [ ] Coordinator proves it with one real `omi run --tool codex` in a sandbox using the PO's ChatGPT login (DONE, tests pass, Usage row `(codex)`).
- [ ] README "Lấy và lưu key": add the ChatGPT-subscription option.

## Checkpoint
Done: tool_secret/codex_login (order key, env, ChatGPT login; JWT exp check), OMI_CODEX_AUTH boot wrapper, chatgpt.com allowlist, README, tests.
Not done: real run (Coordinator).
Tests: python3 tests/test_omi.py ok.
Next: Coordinator real `omi run --tool codex`.

Coordinator probe 2026-10-26 (real runs in the worker image, codex 0.164.0, PO's ChatGPT login):
- `codex login --with-access-token` does NOT take the ChatGPT OAuth access token: it expects an "agent identity JWT" (error "agent identity JWT payload is not valid JSON"). Do not use it.
- Env name `CODEX_ACCESS_TOKEN` is read by codex itself as the agent identity token; never use that name. `OMI_CODEX_AUTH` works.
- Works: host builds `{"auth_mode":"chatgpt","OPENAI_API_KEY":null,"last_refresh":<host value>,"tokens":{"access_token","id_token","account_id" from host auth.json, "refresh_token":"omi-no-refresh"}}` (placeholder because the schema requires the field: "missing field `refresh_token`"), passes it as `-e OMI_CODEX_AUTH`; container: `mkdir -p $HOME/.codex && printenv OMI_CODEX_AUTH > $HOME/.codex/auth.json && chmod 600 ... && unset OMI_CODEX_AUTH`, then `codex exec` -> "Logged in using ChatGPT", reply PONG, 1,839 tokens.
- Allowlist: `chatgpt.com` is enough (PONG with only chatgpt.com + api.openai.com). Blocked and harmless: ab.chatgpt.com, *.oaiusercontent.com, github.com, api.github.com, files.openai.com.
- Expired access token: not observed yet; with the placeholder the container cannot refresh, so expect an auth error -> message "run `codex` once on the host, then retry".
Architect step skipped: the approach is proven by these runs.
Coordinator real run 2026-10-26 (fresh sandbox, this worktree's code, PO's ChatGPT login, no API key stored): `omi run omi-agent-engineer TASK-001 --tool codex` -> `tool: codex (codex-default)`, DONE, slugify correct, sandbox tests pass, Usage row `| omi-agent-engineer | codex-default (codex) | medium | 115922 | 1040 | 110720 | 37s |`. Noted: the image has `python3` but no `python`, so codex could not run the config's literal `python tests/...` (it ran python3).
## Steps
- plan started 2026-10-26 11:19
- plan done 2026-10-26 11:19
- architect started 2026-10-26 11:19
- architect skipped 2026-10-26 11:22: approach proven by Coordinator probe runs recorded in the Checkpoint
- build started 2026-10-26 11:22
- build done 2026-10-26 11:25
- review started 2026-10-26 11:25
- review done 2026-10-26 11:27
- security started 2026-10-26 11:27

## Reports
2026-10-26 11:24 omi-agent-engineer (claude):
> DONE
> - I changed `src/omi/__init__.py`, `tests/test_omi.py`, `README.md` and `.omi/tasks/TASK-065.md` (checkpoint). The Dockerfile needed no change.
> - **Secret order:** a new `tool_secret()` tries the stored key, then env `OPENAI_API_KEY`, then the host ChatGPT login. `codex_login()` reads `$CODEX_HOME/auth.json` at run time and keeps only the access token, id token and account id.
> - **Container side:** the refresh token is replaced by the `omi-no-refresh` placeholder, and the slim JSON goes in as `-e OMI_CODEX_AUTH` (name only in argv). A `sh -c` wrapper writes `~/.codex/auth.json` into the tmpfs home, unsets the variable, then runs `codex exec`. `chatgpt.com` is added to the allowlist only in ChatGPT mode.
> - **Errors:** a missing or expired login (the JWT `exp` is checked) exits with "run `codex` once on the host (or `codex login`) and retry". The Claude path and the API-key path are unchanged.
> - **Tests:** `python3 tests/test_omi.py` passes. New tests cover the secret order, the missing and expired cases, no token value in argv, and the allowlist. The existing quota test now expects "no ChatGPT login" instead of "no codex token", and the suite sets `CODEX_HOME` to an empty temp dir so it never reads a real login.
> - **Open:** the real `omi run --tool codex` with the PO's login is still for the Coordinator, so the Usage row `(codex)` is not confirmed. I never saw a real expired-token error from codex, so only the local expiry check is tested.
> 
> Suggested commit: `feat(codex): run Codex in the worker with the host ChatGPT login`
2026-10-26 11:26 omi-agent-reviewer (claude):
> VERDICT: PASS
> - No blocking findings.
> - `.omi/tasks/TASK-065.md` is edited outside the listed `scope`. This is the task's own checkpoint and report file, so I'm not counting it as a defect.
> - I could not rerun the real `omi run --tool codex`, because docker is missing in this container. The last AC rests on the Coordinator's recorded run in the task file.
> - Tests: `python3 tests/test_omi.py` ends with `ok`.
> 
> AC: Secret order is stored key, then env `OPENAI_API_KEY`, then the host ChatGPT login read at run time, never stored or logged ✓ `tool_secret` and `codex_login` (`__init__.py:894-933`) read `$CODEX_HOME/auth.json` on each call. `test_codex_chatgpt_login` covers the env key winning over the login.
> AC: ChatGPT mode passes the token by env name only, the container writes a slim `auth.json` before `codex exec`, and `chatgpt.com` is allowlisted only in this mode ✓ `-e OMI_CODEX_AUTH` carries the name only, and the `CODEX_AUTH_BOOT` wrapper writes the file, unsets the variable and runs `exec "$@"`. The refresh token becomes the `omi-no-refresh` placeholder, per the Coordinator probe. `allow_for(..., chatgpt=True)` adds `chatgpt.com` only for codex. `test_codex_chatgpt_run` asserts the token and `REAL-REFRESH` are absent from argv, and that the wrapper is present.
> AC: Missing or expired login gives a clear message, the API-key and Claude paths are unchanged, and tests cover the secret order, argv and the missing/expired cases ✓ The message says to run `codex` once on the host (or `codex login`) and retry. The expiry check reads the JWT `exp`. The quota-fallback path now uses `tool_secret(other)` and reports the login problem. The tests cover missing, expired, valid, env-first and argv.
> [... truncated ...]
> AC: README "Lấy và lưu key" gains the ChatGPT-subscription option ✓ A new bullet at `README.md:33` gives the order, the `OMI_CODEX_AUTH` name, the refresh-token guarantee and the allowlist note.
2026-10-26 11:29 omi-agent-security-reviewer (claude):
> ```
> VERDICT: PASS
> - No blocking findings. `python3 tests/test_omi.py` ends with `ok`.
> - What I checked: no token value appears in argv. `worker_argv` (`src/omi/__init__.py:1153`) passes only `-e OMI_CODEX_AUTH`, and `test_codex_chatgpt_run` asserts that neither the access token nor `REAL-REFRESH` is in argv. The refresh token is replaced by the `omi-no-refresh` placeholder (`__init__.py:921-923`).
> - The `sh -c BOOT sh codex…` wrapper is correct: `$0`=sh and `"$@"`=codex. The Dockerfile has no ENTRYPOINT, and `auth.json` lands on the `/home/node` tmpfs, which is noexec and owned by uid 1000. `proxy.py:2` matches hosts exactly on port 443, so adding `chatgpt.com` does not open its subdomains.
> - When the quota limit is hit, `tool_secret(other)` returns a tuple, and both `attempt()` and the `[1]`/`[2]` checks unpack it correctly (`__init__.py:1690-1707`). The Claude path and the API-key path keep their order and env names.
> - Remaining risk, not a regression: the codex agent runs with `--dangerously-bypass-approvals-and-sandbox` and can read `~/.codex/auth.json`. It could copy the ChatGPT access token into the rw `/work` diff or send it to an allowlisted host. Before this change the API key was just as readable through `printenv`.
> UNVERIFIED: how codex 0.164.0 behaves on an expired token inside the container. The recorded probe never saw it, and confirming it needs a real run with an expired token, which needs docker and network.
> ```

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 22 | 8897 | 405837 | 76s | 3/3 omi-skill-docker-worker-pitfalls omi-skill-windows-powershell omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 8 | 1914 | 110667 | 38s | - | PASS 26c309e |
| omi-agent-security-reviewer | claude-opus-5-5 | high | 16 | 3708 | 249980 | 64s | 2/2 omi-skill-diff-security-review omi-skill-ci-workflow-audit | PASS e77182c |
