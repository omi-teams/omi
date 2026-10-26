---
id: TASK-040
title: Usage metering per worker run and per task
status: done
depends: TASK-028
scope: src/omi/__init__.py, src/omi/template/**, .omi/tasks/_template.md, tests/**, AGENTS.md
---
## Goal
Real token numbers instead of estimates, recorded where the PO and later tasks can read them.

## Acceptance criteria
- [x] Every `omi run`/`omi worker` run records input, output and cache tokens, model, effort and duration in the task file (a short `## Usage` table); numbers come from the harness output, not estimates. If a harness gives no numbers, record `n/a`.
- [x] `python -m omi status` shows per-task totals and review rounds; AGENTS.md grows by at most 1 line.
- [x] Tests with a fake harness output; `python tests/test_omi.py` passes.

## Checkpoint
Done: usage parse/record/totals in src/omi/__init__.py (claude --output-format json, codex --json); status shows totals+review rounds; 1 line in AGENTS.md (+template copy); test_usage.
Not done: nothing.
Tests: python tests/test_omi.py ok
Next: TASK-029
