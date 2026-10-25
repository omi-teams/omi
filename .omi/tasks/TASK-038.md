---
id: TASK-038
title: Wire workflows into omi-idea, omi-task and AGENTS.md
status: planned
depends: TASK-040, TASK-033, TASK-034, TASK-035, TASK-036, TASK-037
scope: .claude/skills/**, src/omi/template/**, AGENTS.md, README.md, tests/**, src/omi/__init__.py
---
## Goal
The Coordinator picks a workflow at planning time and follows it step by step.

## Acceptance criteria
- [ ] omi-idea / omi-task choose the lightest fitting workflow from the catalog and write `workflow:` into the task; omi-task drives it with `omi step`.
- [ ] AGENTS.md grows by at most 4 lines; the catalogs are the only workflow text loaded by default.
- [ ] Resume works: after an interruption `omi status` shows the task step and the Coordinator continues from it.
- [ ] Template and root copies identical; `python tests/test_omi.py` passes.

- [ ] Carry-over from the TASK-033 review: `omi-flow-feature-ui` "Use instead" for a UI change in a sensitive area has no actionable path; say the Coordinator runs `omi-flow-feature-sensitive` and inserts the `design` and `qa` steps.

- [ ] `omi run <role> <ID>` adds the current step's skills (when the task has `step:` and the step role matches) to the role defaults and task skills, so the step skill is in the prompt, budget-checked, and shown in the Usage `skills read` cell. Test it.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-041
