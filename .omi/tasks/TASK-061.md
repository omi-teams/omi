---
id: TASK-061
title: Fair baseline for omi-agent-architect
status: in-progress
depends: TASK-057
scope: docs/research/omi-eval.md, .omi/tasks/**
role: omi-agent-docs-writer
skills: []
workflow: omi-flow-spike
step: write
---
## Goal
TASK-057's architect baseline was invalid (a review prompt was used). Re-run the change-request scenario with the architect role and with a plain "give 2-3 options and one recommendation" prompt, same model (opus/high), and record the numbers.

## Acceptance criteria
- [ ] Both runs in a fresh sandbox, same task, same model and effort; correctness (2-3 options, exactly one recommended, reason) plus out/cache tokens and seconds recorded.
- [ ] docs/research/omi-eval.md gets the result and a keep/rework proposal for the architect role; the PO decides.

## Checkpoint
Done: appended "Baseline architect (TASK-061)" section to docs/research/omi-eval.md (Vietnamese, nothing replaced; supersedes invalid TASK-057 architect baseline) with both runs' numbers and keep proposal for PO.
Not done: none in docs scope. Runs were executed by Coordinator; not re-run here.
Tests: not run (docs-only; `python3 tests/test_omi.py` not applicable to this change).
Next: Coordinator reviews the diff and commits; PO decides on architect keep.

Coordinator results 2026-10-26 (fresh sandbox, same task, opus/high, n=1; out / cache / sec): architect role + change-request skill 1610 / 76389 / 26s; plain options prompt 2185 / 51628 / 29s. Both correct: 3 options with cost and risk, one recommended (both chose A: switch in place, ValueError on page<0). Architect adds what the plain run did not: a task split with model picks, the scope gap (task scope .omi/tasks/** cannot hold the code change) and a duplicate-task warning, in the fixed RECOMMEND/OPTIONS/STRUCTURE/RISKS/TASKS format. Cost: -26% output, +48% cache. Proposal: keep the architect role (its structure feeds the Coordinator's replan); the PO decides.
Write (docs-writer): append a Vietnamese section "Baseline architect (TASK-061)" to docs/research/omi-eval.md with these numbers, replacing nothing; note that it supersedes the invalid TASK-057 architect baseline.
## Steps
- plan started 2026-10-26 11:02
- plan done 2026-10-26 11:02
- research started 2026-10-26 11:02
- research skipped 2026-10-26 11:04: evidence is the two Coordinator-run sandbox runs recorded in the Checkpoint
- write started 2026-10-26 11:04

## Reports
2026-10-26 11:04 omi-agent-docs-writer (claude):
> DONE
> Files: docs/research/omi-eval.md (appended "Baseline architect (TASK-061)", Vietnamese, nothing replaced); .omi/tasks/TASK-061.md (Checkpoint updated)
> Commit: docs: add architect baseline re-run results to omi eval
> Not verified: numbers are the Coordinator's n=1 runs, taken from the task file; I did not re-run them. Tests not run (docs-only).
> Open: n=1, and the architect variant also includes the change-request skill, so the role's own effect is not isolated. PO decides keep for architect; I recommend keep.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-docs-writer | claude-haiku-5-5 | low | 10 | 2630 | 100929 | 19s | - | - |
