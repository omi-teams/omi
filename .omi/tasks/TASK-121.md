---
id: TASK-121
title: Coordinator proposes tool, model and effort; PO only approves
status: in-progress
depends:
plan:
scope: src/omi/template/AGENTS.md, src/omi/template/dot-claude/skills/**, src/omi/template_shas.json, AGENTS.md, .claude/skills/**, tests/test_tools.py, .omi/tasks/TASK-121.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature
step:
---
## Goal
In every omi project, the Coordinator picks the fitting tool, model and effort for a task itself and presents it as one proposal for the PO to approve, with the other tool as the alternative; the PO no longer works out model or effort.

## Acceptance criteria
- [ ] `## Task-start tool choice` in the template AGENTS.md (and the omi-task skill copy) says: the Coordinator decides tool, concrete model and effort from the quota rules and `## Models`, presents it first as "Approve: <tool> (<model>/<effort>) — <task-specific reason>", lists the other tool with its concrete model/effort as the alternative, and records the approved choice in the task; it no longer says "offer both tools and wait for the PO to choose".
- [ ] When the PO names only a tool, the Coordinator chooses model and effort itself and states them, without another question; never `codex-default` or an omitted effort.
- [ ] The repo's own `AGENTS.md` and `.claude/skills/omi-task/SKILL.md` match the template; `template_shas.json` is updated if the template hashes require it.
- [ ] `tests/test_tools.py` checks the new wording instead of "PO chooses"; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
