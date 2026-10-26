---
id: TASK-045
title: Codex CLI in the worker image
status: in-progress
depends: TASK-028
scope: src/omi/template/docker/**, src/omi/template/dot-omi/config.json, src/omi/__init__.py, tests/**, README.md
skills: [omi-skill-docker-worker-pitfalls, omi-skill-windows-powershell]
role: omi-agent-engineer
workflow: omi-flow-feature-sensitive
---
## Goal
`omi run --tool codex` works in the container with a pinned Codex CLI version.

## Acceptance criteria
- [ ] The Dockerfile installs a pinned Codex CLI version; the pin is recorded in config and README.
- [ ] `omi run <role> <TASK> --tool codex` runs `codex exec -m <model> -c model_reasoning_effort=<level>` in the container with the key passed by name only.
- [ ] The Claude image path is unchanged; `python tests/test_omi.py` passes.

- [ ] Follow-up from incident TASK-053: `omi worker --prove` names its run like a real one (`container_name` with a real role, model and effort, so 60+ chars) and checks that the CLI in the image reaches its API host through the proxy (no token needed: expect an auth error, not a DNS or network error).

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-040
