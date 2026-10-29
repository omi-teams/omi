---
id: TASK-101
title: Pilot detached mode on omi-pilot-splitbill
status: in-progress
depends: TASK-099, TASK-100
plan: PLAN-004
scope: docs/pilot-detached.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-docs-only
step: write
---
## Goal
Prove the spec's success criteria on real runs and write the evidence down; gaps found become decisions for a later plan.

## Acceptance criteria
- [ ] On a fresh clone of omi-pilot-splitbill: `omi install-user`, `omi attach`, one real task from start to merge. Evidence: `git log` and `git status` of the code repo show only the task's code commit and no omi file.
- [ ] A second clone of omi-state in another dir (`OMI_STATE`) gives the same `omi status`.
- [ ] `docs/pilot-detached.md` (Vietnamese) lists each criterion with the command run and its output, and every gap found.
- [ ] In-repo mode: the full test suite passes on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:

## Steps
- plan started 2026-10-29 13:18
- plan done 2026-10-29 13:18
- write started 2026-10-29 13:18
