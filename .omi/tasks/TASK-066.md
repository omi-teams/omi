---
id: TASK-066
title: Agents cannot change step or status in the task file
status: in-progress
depends: TASK-064
scope: src/omi/__init__.py, tests/**
role: omi-agent-engineer
skills: []
workflow: omi-flow-bugfix
step:
---
## Goal
Bug: in TASK-064 the engineer wrote `step: done` into the task frontmatter, which broke `omi step` until the Coordinator restored it. `step:` and `status:` are Coordinator-owned (set by `omi step` and by the Coordinator).

## Acceptance criteria
- [ ] After an agent run, `omi run` compares the task file's `step`, `status`, `workflow`, `scope`, `role` and `skills` frontmatter with the values before the run; any change is reverted and reported as `REVERTED: <field>` (the rest of the file, e.g. Checkpoint, is kept).
- [ ] Test: an agent run that edits `step:` and the Checkpoint keeps the Checkpoint edit and restores `step:`.
- [ ] `python tests/test_omi.py` passes.

## Checkpoint
Done:
Not done:
Tests:
Next:
