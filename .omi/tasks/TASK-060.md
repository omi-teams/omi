---
id: TASK-060
title: Stream the agent's stderr live again
status: in-progress
depends: TASK-056
scope: src/omi/__init__.py, tests/**
role: omi-agent-engineer
skills: []
workflow: omi-flow-feature
step: build
---
## Goal
Since TASK-056, `omi run` buffers the agent container's stderr and prints it only after exit. Stream it live again while keeping the exact name-conflict retry.

## Acceptance criteria
- [ ] Agent stderr reaches the terminal while the container runs (e.g. a reader thread that echoes each line and keeps a copy), and is not lost if `omi run` is interrupted.
- [ ] The name-conflict retry still triggers only on Docker's exact conflict message for that name (docker run exits 125 before the agent starts); a test covers both live echo and the retry.
- [ ] `python tests/test_omi.py` passes.

## Checkpoint
Done: run_once uses Popen + stderr reader thread (live echo, copy kept for name_taken); tests: FakePopen, live-echo assert, existing retry tests.
Not done: -
Tests: python3 tests/test_omi.py ok
Next: review/commit

## Steps
- plan started 2026-10-26 10:59
- plan done 2026-10-26 10:59
- build started 2026-10-26 10:59

## Reports
2026-10-26 11:00 omi-agent-engineer (claude):
> DONE
> - Files: `src/omi/__init__.py`, `tests/test_omi.py`, `.omi/tasks/TASK-060.md` (checkpoint).
> - `run_once` now starts the container with `Popen`. A daemon thread echoes each stderr line as it arrives and keeps a copy. The conflict retry still checks that copy with `name_taken` (exact message, non-zero exit), so port clashes don't rerun the agent. I didn't write a test for the interrupt case; each line is echoed as it arrives, so nothing waits on exit.
> - A conflict message is also echoed live before the retry, because it can't be known in advance. That's a small cosmetic side effect.
> - Tests: the new `FakePopen` in `tests/test_omi.py` routes `docker run` to the existing mocked `subprocess.run` results, so the old retry and port-clash tests still apply. A new assertion checks that stderr is echoed line by line. `python3 tests/test_omi.py` passes.
> - Suggested commit: `fix(run): stream agent stderr live while keeping exact name-conflict retry`

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 18 | 4445 | 238430 | 56s | 1/1 omi-skill-lean-implementation | - |
