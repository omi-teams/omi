---
id: TASK-084
title: Agents in the worker can run the claude and codex CLIs themselves (logged in, network allowed)
status: in-progress
depends: TASK-083
plan: PLAN-001
scope: src/omi/__init__.py, tests/test_omi.py, docker/**, README.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: opus
effort: high
workflow: omi-flow-feature-sensitive
step:
---
## Goal
In TASK-080/081 a researcher inside the Docker worker ran `claude -p --model haiku "say ok"` and got "Not logged in · Please run /login" even though the agent itself was a logged-in claude; `codex login status` said "Not logged in" (`~/.codex` empty) and the proxy blocked `api.openai.com` / `chatgpt.com`. A model-probe spike must be able to call the CLI of the run's own tool from inside the worker, with the same credentials the agent already has, and without new exposure of secrets.

## Acceptance criteria
- [ ] Root cause written in the Checkpoint for both tools (why a nested `claude -p` in the container is not logged in although the agent is; what codex needs: auth file, network hosts).
- [ ] In a worker run with tool claude, a nested `claude -p --model haiku --effort low "say ok"` answers `ok`; with tool codex, a nested `codex exec -m gpt-6-luna -c model_reasoning_effort=low "say ok"` answers `ok`. Proven by one real run each, output pasted in the Checkpoint.
- [ ] Only the running tool's own credentials enter the container (no claude secret in a codex run and vice versa); secrets stay out of argv, image layers and the worktree; the network allow-list grows only by that tool's own API/login hosts.
- [ ] Tests in `tests/test_omi.py` cover the env/mount and network-allow construction for each tool; README notes that nested CLI calls use the run's own login.

## Checkpoint
Done:
Not done:
Tests:
Next:
