---
id: TASK-107
title: attach pushes state and prepares development
status: planned
depends: 
plan: PLAN-005
scope: src/omi/upgrade.py, src/omi/state_sync.py, tests/test_omi.py, README.md
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
Pilot gaps G2 and G3: after `omi attach` the state is on its remote and the code clone has a local `development` branch, with no manual step.

## Acceptance criteria
- [ ] With a state remote, `omi attach` pushes its commit (sets upstream on an empty remote); a push failure keeps the commit and prints `STATE NOT PUSHED: run omi sync`.
- [ ] If `origin/development` exists and no local `development` does, attach creates it tracking origin and prints one line; an existing local branch is untouched; the code repo gets no commit and no file.
- [ ] Unit tests cover push success, push failure, empty remote, branch created and branch already present; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
