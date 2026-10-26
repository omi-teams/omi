---
id: TASK-060
title: Stream the agent's stderr live again
status: in-progress
depends: TASK-056
scope: src/omi/__init__.py, tests/**
role: omi-agent-engineer
skills: []
workflow: omi-flow-feature
step:
---
## Goal
Since TASK-056, `omi run` buffers the agent container's stderr and prints it only after exit. Stream it live again while keeping the exact name-conflict retry.

## Acceptance criteria
- [ ] Agent stderr reaches the terminal while the container runs (e.g. a reader thread that echoes each line and keeps a copy), and is not lost if `omi run` is interrupted.
- [ ] The name-conflict retry still triggers only on Docker's exact conflict message for that name (docker run exits 125 before the agent starts); a test covers both live echo and the retry.
- [ ] `python tests/test_omi.py` passes.

## Checkpoint
Done:
Not done:
Tests:
Next:
