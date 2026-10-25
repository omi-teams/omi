---
id: TASK-038
title: Wire workflows into omi-idea, omi-task and AGENTS.md
status: planned
depends: TASK-040, TASK-033, TASK-034, TASK-035, TASK-036, TASK-037
scope: .claude/skills/**, src/omi/template/**, AGENTS.md, README.md, tests/**
---
## Goal
The Coordinator picks a workflow at planning time and follows it step by step.

## Acceptance criteria
- [ ] omi-idea / omi-task choose the lightest fitting workflow from the catalog and write `workflow:` into the task; omi-task drives it with `omi step`.
- [ ] AGENTS.md grows by at most 4 lines; the catalogs are the only workflow text loaded by default.
- [ ] Resume works: after an interruption `omi status` shows the task step and the Coordinator continues from it.
- [ ] Template and root copies identical; `python tests/test_omi.py` passes.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-041
