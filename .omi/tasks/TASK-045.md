---
id: TASK-045
title: Codex CLI in the worker image
status: planned
depends: TASK-028
scope: src/omi/template/docker/**, src/omi/__init__.py, tests/**, README.md
skills: [omi-skill-docker-worker-pitfalls, omi-skill-windows-powershell]
---
## Goal
`omi run --tool codex` works in the container with a pinned Codex CLI version.

## Acceptance criteria
- [ ] The Dockerfile installs a pinned Codex CLI version; the pin is recorded in config and README.
- [ ] `omi run <role> <TASK> --tool codex` runs `codex exec -m <model> -c model_reasoning_effort=<level>` in the container with the key passed by name only.
- [ ] The Claude image path is unchanged; `python tests/test_omi.py` passes.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-040
