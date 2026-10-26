---
id: TASK-045
title: Codex CLI in the worker image
status: in-progress
depends: TASK-028
scope: src/omi/template/docker/**, src/omi/template/dot-omi/config.json, src/omi/__init__.py, tests/**, README.md
skills: [omi-skill-docker-worker-pitfalls, omi-skill-windows-powershell]
role: omi-agent-engineer
workflow: omi-flow-feature-sensitive
step: build
---
## Goal
`omi run --tool codex` works in the container with a pinned Codex CLI version.

## Acceptance criteria
- [ ] The Dockerfile installs a pinned Codex CLI version; the pin is recorded in config and README.
- [ ] `omi run <role> <TASK> --tool codex` runs `codex exec -m <model> -c model_reasoning_effort=<level>` in the container with the key passed by name only.
- [ ] The Claude image path is unchanged; `python tests/test_omi.py` passes.

- [ ] Follow-up from incident TASK-053: `omi worker --prove` names its run like a real one (`container_name` with a real role, model and effort, so 60+ chars) and checks that the CLI in the image reaches its API host through the proxy (no token needed: expect an auth error, not a DNS or network error).

## Checkpoint
Done: Dockerfile codex pin 0.46.0, config cli_versions + api.openai.com, README, prove.sh CLI auth checks, worker --prove name, tests
Not done: real docker run of --prove (no docker here); codex version 0.46.0 unverified (no npm access)
Tests: python3 tests/test_omi.py ok
Next: TASK-040
Coordinator real run FAIL (`omi worker <wt> --prove` on Docker Desktop, codex 0.46.0 exists on npm):
1. `NETWORK BLOCKED: api.openai.com:443`: the repo's own `.omi/config.json` only allows api.anthropic.com, so the template change is not enough. Add each tool's API host to the allow list in code (architect option A: tool table with `api_host`, dedup with `network_allow`) for `--prove` and for `omi run --tool codex`; claude path allow list unchanged.
2. codex network failure prints `error sending request for url (...)` / `stream error`; add it to the network-error patterns (it was only caught as "unexpected output").
3. `--prove` exited 0 with a FAIL line: it must exit non-zero when any line starts with FAIL, and also when no `PASS claude CLI`/`PASS codex CLI` line appears (project-owned prove.sh). Add tests.

## Steps
- plan started 2026-10-26 09:02
- plan done 2026-10-26 09:02
- architect started 2026-10-26 09:02
- architect done 2026-10-26 09:04
- build started 2026-10-26 09:04

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 12 | 7743 | 171921 | 93s | - | n/a |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 18 | 5637 | 301884 | 73s | 3/3 omi-skill-docker-worker-pitfalls omi-skill-windows-powershell omi-skill-lean-implementation | - |
