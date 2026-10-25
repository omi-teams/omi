---
id: TASK-048
title: Run tasks through their workflow steps with step skills
status: in-progress
depends: TASK-033, TASK-047
scope: src/omi/__init__.py, tests/**, .claude/skills/omi-task/**, src/omi/template/**
role: omi-agent-engineer
skills: [omi-skill-lean-implementation]
---
## Goal
Make workflows real before the remaining workflow tasks: omi-task drives each task through `omi step`, and `omi run` gives the agent the current step's skills, so the Usage and `## Steps` logs prove which skills were loaded and which steps ran.

## Acceptance criteria
- [ ] `omi run <role> <ID>` adds the current step's skills (when the task has `step:` and the step role matches) to the role defaults and task skills, so the step skill is in the prompt, budget-checked, and shown in the Usage `skills read` cell. Test it.
- [ ] The role prompt names the test command (`Tests: <test_command(...)>`), so roles stop guessing pytest; the host already runs it before read roles.
- [ ] omi-task (root and template copy, identical) drives the task with `python -m omi step <ID> next|done` around each step of its `workflow:` (default `omi-flow-feature`); `coordinator` steps are done by the Coordinator; a `po` gate step records `PO approval <step>: <PO's words>` in `## Steps` before `done`. Keep the skill file short: it may replace existing lines, net growth at most 6 lines.
- [ ] `python -m omi status` shows the current `step:` next to an in-progress task.
- [ ] `python tests/test_omi.py` passes.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-036 (first task run through its workflow)
