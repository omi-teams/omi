---
id: TASK-065
title: Run Codex in the worker with the PO's ChatGPT login (no API key)
status: in-progress
depends: TASK-054
scope: src/omi/__init__.py, src/omi/template/docker/**, tests/**, README.md
role: omi-agent-engineer
skills: [omi-skill-docker-worker-pitfalls, omi-skill-windows-powershell]
workflow: omi-flow-feature-sensitive
step:
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
