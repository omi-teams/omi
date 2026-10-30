---
id: TASK-135
title: Move the omi repo to detached mode on omi-state
status: planned
depends: TASK-137
plan: PLAN-007
scope: .omi/tasks/TASK-135.md, docs/**
role: omi-agent-engineer
skills: []
refs: []
tool:
model:
effort:
step_settings:
workflow: omi-flow-feature-sensitive
step:
---
## Goal
The omi repo's own plans, tasks and decisions live in `projects/omi/` on GitHub omi-teams/omi-state (`omi attach`), so they appear on the board like every other project; GitHub omi-state is the single source of omi state.

## Acceptance criteria
- [ ] `omi attach` registers this repo; `.omi/tasks`, `.omi/plans`, `.omi/decisions.md`, config, rules, skills and catalogs are copied to `projects/omi/` with history noted, committed and pushed to omi-state; `omi status` from the code repo gives the same output before and after.
- [ ] The in-repo omi state files are removed from the code repo in one PR (the `src/omi/template/**` copies stay); `omi status` prints no `WARN: in-repo omi files ignored` line.
- [ ] A fresh clone of omi-state shows project `omi` with PLAN-007 on the board.
- [ ] `docs/pilot-detached.md` (Vietnamese) records the migration commands and their output, and the rollback (restore the in-repo files from the commit before removal).

## Checkpoint
Done:
Not done:
Tests:
Next: architect decides which in-repo files (AGENTS.md, .claude/) stay for developing omi itself; scope widened from that.
