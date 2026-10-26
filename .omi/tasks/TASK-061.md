---
id: TASK-061
title: Fair baseline for omi-agent-architect
status: in-progress
depends: TASK-057
scope: docs/research/omi-eval.md, .omi/tasks/**
role: omi-agent-docs-writer
skills: []
workflow: omi-flow-spike
step: research
---
## Goal
TASK-057's architect baseline was invalid (a review prompt was used). Re-run the change-request scenario with the architect role and with a plain "give 2-3 options and one recommendation" prompt, same model (opus/high), and record the numbers.

## Acceptance criteria
- [ ] Both runs in a fresh sandbox, same task, same model and effort; correctness (2-3 options, exactly one recommended, reason) plus out/cache tokens and seconds recorded.
- [ ] docs/research/omi-eval.md gets the result and a keep/rework proposal for the architect role; the PO decides.

## Checkpoint
Done:
Not done:
Tests:
Next:

Coordinator results 2026-10-26 (fresh sandbox, same task, opus/high, n=1; out / cache / sec): architect role + change-request skill 1610 / 76389 / 26s; plain options prompt 2185 / 51628 / 29s. Both correct: 3 options with cost and risk, one recommended (both chose A: switch in place, ValueError on page<0). Architect adds what the plain run did not: a task split with model picks, the scope gap (task scope .omi/tasks/** cannot hold the code change) and a duplicate-task warning, in the fixed RECOMMEND/OPTIONS/STRUCTURE/RISKS/TASKS format. Cost: -26% output, +48% cache. Proposal: keep the architect role (its structure feeds the Coordinator's replan); the PO decides.
Write (docs-writer): append a Vietnamese section "Baseline architect (TASK-061)" to docs/research/omi-eval.md with these numbers, replacing nothing; note that it supersedes the invalid TASK-057 architect baseline.
## Steps
- plan started 2026-10-26 11:02
- plan done 2026-10-26 11:02
- research started 2026-10-26 11:02
