---
id: TASK-048
title: Run tasks through their workflow steps with step skills
status: done
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
Coordinator check before review, fix (edit only `## Checkpoint` here):
1. `omi step` writes the main-checkout task file, but `omi run` reads the worktree copy, so in a real run `step:` never reaches `run_role` and step skills never load. Keep per-task step state in the task's worktree copy: `omi step` writes `<wt>/.omi/tasks/<ID>.md` when the task has a worktree (`task_worktrees`), else the main checkout; `omi status` shows `step:` from the worktree copy for in-progress tasks. The step log then merges with the task branch.
2. Use `DEFAULT_WORKFLOW` instead of the literal `"omi-flow-feature"` in `run_role`.
3. Test with a real worktree layout: `omi step next` from the main checkout, then `run_role` on the worktree sees the step skill; `omi status` shows the step.
Done: all criteria (step skills in run_role, Tests: line, omi-task both copies +2 lines, status shows step)
Not done: -
Tests: python3 tests/test_omi.py ok
Fix round: step writes the worktree copy (task_worktrees), run_role uses DEFAULT_WORKFLOW, test with mocked worktree layout; status shows step via tasks() worktree copy.
Next: TASK-036 (first task run through its workflow)

## Usage
| role | model | effort | input | output | cache | duration | skills read |
|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 34 | 7236 | 643285 | 138s | 1/1 omi-skill-lean-implementation |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 18 | 2662 | 237405 | 37s | 1/1 omi-skill-lean-implementation |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 8 | 1898 | 97647 | 27s | 1/1 omi-skill-lean-implementation |
