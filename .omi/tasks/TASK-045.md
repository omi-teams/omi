---
id: TASK-045
title: Codex CLI in the worker image
status: done
depends: TASK-028
scope: src/omi/template/docker/**, src/omi/template/dot-omi/config.json, src/omi/__init__.py, tests/**, README.md
skills: [omi-skill-docker-worker-pitfalls, omi-skill-windows-powershell]
role: omi-agent-engineer
workflow: omi-flow-feature-sensitive
step: accept
---
## Goal
`omi run --tool codex` works in the container with a pinned Codex CLI version.

## Acceptance criteria
- [x] The Dockerfile installs a pinned Codex CLI version; the pin is recorded in config and README.
- [x] `omi run <role> <TASK> --tool codex` runs `codex exec -m <model> -c model_reasoning_effort=<level>` in the container with the key passed by name only.
- [x] The Claude image path is unchanged; `python tests/test_omi.py` passes.

- [x] Follow-up from incident TASK-053: `omi worker --prove` names its run like a real one (`container_name` with a real role, model and effort, so 60+ chars) and checks that the CLI in the image reaches its API host through the proxy (no token needed: expect an auth error, not a DNS or network error).

## Checkpoint
Done: Dockerfile codex pin 0.46.0, config cli_versions + api.openai.com, README, prove.sh CLI auth checks, worker --prove name, tests
Not done: real docker run of --prove (no docker here); codex version 0.46.0 unverified (no npm access)
Tests: python3 tests/test_omi.py ok
Next: TASK-040
Coordinator real run FAIL (`omi worker <wt> --prove` on Docker Desktop, codex 0.46.0 exists on npm):
1. `NETWORK BLOCKED: api.openai.com:443`: the repo's own `.omi/config.json` only allows api.anthropic.com, so the template change is not enough. Add each tool's API host to the allow list in code (architect option A: tool table with `api_host`, dedup with `network_allow`) for `--prove` and for `omi run --tool codex`; claude path allow list unchanged.
2. codex network failure prints `error sending request for url (...)` / `stream error`; add it to the network-error patterns (it was only caught as "unexpected output").
3. `--prove` exited 0 with a FAIL line: it must exit non-zero when any line starts with FAIL, and also when no `PASS claude CLI`/`PASS codex CLI` line appears (project-owned prove.sh). Add tests.

Round 2 done: allow_for adds each tool's api_host (TOOL_API_HOST) for run and --prove; prove.sh network patterns include `error sending request|stream error`; --prove exits non-zero on FAIL line or missing PASS claude/codex CLI (prove_rc); tests added. Tests: python3 tests/test_omi.py ok. Not done: real Docker rerun.

Coordinator real run 2 FAIL: api.openai.com now allowed and exit code 1 works, but codex still `error sending request`. Root cause (verified in a temp image): the image has no `ca-certificates`, so Rust codex fails TLS (node/claude ships its own CAs). With `ca-certificates` codex returns `401 Unauthorized`.
1. Dockerfile: add `ca-certificates` to the existing `apt-get install` line; add a test assertion.
2. prove.sh: remove `stream error` from the network pattern: codex prints `stream error: exceeded retry limit, last status: 401 Unauthorized` on auth failure. Keep `error sending request`. Add a test with that 401 line classified as PASS if practical, else just assert the pattern.
Round 3 done: Dockerfile apt-get installs ca-certificates (test asserts it); prove.sh network pattern drops `stream error` (keeps `error sending request`; test asserts the pattern line lacks it). Tests: python3 tests/test_omi.py ok. Not done: real Docker rerun.
PO change at accept (2026-10-26): fix round 3 before acceptance.
Round 5 done: Dockerfile line `@openai/codex@0.164.0 && npm` space restored (only change). Tests: python3 tests/test_omi.py ok. Not done: real Docker rerun.
Round 4 done: api.openai.com removed from template network_allow (test asserts absent; allow_for still adds it for codex); Codex pin 0.164.0 in Dockerfile, cli_versions, README. Tests: python3 tests/test_omi.py ok. Not done: real Docker rerun.
1. Remove `api.openai.com` from the template `network_allow` (`src/omi/template/dot-omi/config.json`); `allow_for` adds it per tool. Update the test that asserted it there (assert it is absent and `allow_for(..., "codex")` adds it). README line stays "mặc định chỉ api.anthropic.com".
2. Bump the Codex pin to `0.164.0` in Dockerfile, `cli_versions` and README.
Coordinator: Dockerfile line lost its space: `@openai/codex@0.164.0&& npm` -> `@openai/codex@0.164.0 && npm`. Only that fix. Real --prove with 0.164.0 PASS (codex also tries github.com, chatgpt.com, api.github.com; blocked, harmless).
## Steps
- plan started 2026-10-26 09:02
- plan done 2026-10-26 09:02
- architect started 2026-10-26 09:02
- architect done 2026-10-26 09:04
- build started 2026-10-26 09:04
- build done 2026-10-26 09:15
- review started 2026-10-26 09:15
- review done 2026-10-26 09:16
- security started 2026-10-26 09:16
- security done 2026-10-26 09:17
- accept started 2026-10-26 09:17
- PO at accept: "Bỏ khỏi template" + "Nâng lên Codex 0.164.0" -> fix round 3, then review and security again
PO approval accept: "Chạy lại security rồi merge" (security PASS after PO change)
- accept done 2026-10-26 09:25

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 12 | 7743 | 171921 | 93s | - | n/a |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 18 | 5637 | 301884 | 73s | 3/3 omi-skill-docker-worker-pitfalls omi-skill-windows-powershell omi-skill-lean-implementation | - |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 16 | 5076 | 240528 | 49s | 3/3 omi-skill-docker-worker-pitfalls omi-skill-windows-powershell omi-skill-lean-implementation | - |
| omi-agent-engineer | claude-haiku-5-5 | low | 14 | 2908 | 176418 | 29s | 3/3 omi-skill-docker-worker-pitfalls omi-skill-windows-powershell omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 8 | 2534 | 101921 | 35s | - | PASS 3f1b556 |
| omi-agent-security-reviewer | claude-sonnet-5-5 | medium | 6 | 1950 | 76268 | 28s | 2/2 omi-skill-diff-security-review omi-skill-ci-workflow-audit | PASS f3153bd |
| omi-agent-engineer | claude-haiku-5-5 | low | 18 | 3236 | 224246 | 41s | 2/2 omi-skill-docker-worker-pitfalls omi-skill-windows-powershell | - |
| omi-agent-engineer | claude-haiku-5-5 | low | 10 | 1475 | 110991 | 22s | 2/2 omi-skill-docker-worker-pitfalls omi-skill-windows-powershell | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 1686 | 74823 | 26s | - | PASS d19a5d0 |
| omi-agent-security-reviewer | claude-sonnet-5-5 | medium | 6 | 1046 | 76322 | 16s | - | PASS b217144 |
