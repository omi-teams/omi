---
id: TASK-061
title: Fair baseline for omi-agent-architect
status: in-progress
depends: TASK-057
scope: docs/research/omi-eval.md, .omi/tasks/**
role: omi-agent-docs-writer
skills: []
workflow: omi-flow-spike
step:
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
