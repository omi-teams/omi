---
id: TASK-065
title: Run Codex in the worker with the PO's ChatGPT login (no API key)
status: in-progress
depends: TASK-054
scope: src/omi/__init__.py, src/omi/template/docker/**, tests/**, README.md
role: omi-agent-engineer
skills: [omi-skill-docker-worker-pitfalls, omi-skill-windows-powershell]
workflow: omi-flow-feature-sensitive
step: architect
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
Done:
Not done:
Tests:
Next:

Coordinator probe 2026-10-26 (real runs in the worker image, codex 0.164.0, PO's ChatGPT login):
- `codex login --with-access-token` does NOT take the ChatGPT OAuth access token: it expects an "agent identity JWT" (error "agent identity JWT payload is not valid JSON"). Do not use it.
- Env name `CODEX_ACCESS_TOKEN` is read by codex itself as the agent identity token; never use that name. `OMI_CODEX_AUTH` works.
- Works: host builds `{"auth_mode":"chatgpt","OPENAI_API_KEY":null,"last_refresh":<host value>,"tokens":{"access_token","id_token","account_id" from host auth.json, "refresh_token":"omi-no-refresh"}}` (placeholder because the schema requires the field: "missing field `refresh_token`"), passes it as `-e OMI_CODEX_AUTH`; container: `mkdir -p $HOME/.codex && printenv OMI_CODEX_AUTH > $HOME/.codex/auth.json && chmod 600 ... && unset OMI_CODEX_AUTH`, then `codex exec` -> "Logged in using ChatGPT", reply PONG, 1,839 tokens.
- Allowlist: `chatgpt.com` is enough (PONG with only chatgpt.com + api.openai.com). Blocked and harmless: ab.chatgpt.com, *.oaiusercontent.com, github.com, api.github.com, files.openai.com.
- Expired access token: not observed yet; with the placeholder the container cannot refresh, so expect an auth error -> message "run `codex` once on the host, then retry".
Architect step skipped: the approach is proven by these runs.
## Steps
- plan started 2026-10-26 11:19
- plan done 2026-10-26 11:19
- architect started 2026-10-26 11:19
