---
id: TASK-110
title: Document Windows PATH, test command and worker hosts for detached mode
status: planned
depends: TASK-108, TASK-109
plan: PLAN-005
scope: README.md, .omi/tasks/TASK-110.md
role: omi-agent-engineer
skills: []
refs: []
tool:
model:
effort:
step_settings:
workflow: omi-flow-feature
step:
---
## Goal
Pilot gaps G1 and G7: README tells a new user what the pilot had to find out.

## Acceptance criteria
- [ ] README says how to put the Python `Scripts` dir on PATH on Windows (or use `python -m omi`), that an attached project needs `test` set in its state `.omi/config.json`, and that the worker adds the selected tool's API host (and chatgpt.com for a ChatGPT login) besides `network_allow`; it also documents the TASK-108 in-repo files warning and `omi step <ID> approve|reopen --why`; the `cli.py` usage line is left to TASK-111.
- [ ] At most 12 added lines, Vietnamese, matching README style.

## Checkpoint
Done:
Not done:
Tests:
Next:
