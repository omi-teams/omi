---
id: TASK-031
title: Roles - delivery (devops, docs-writer)
status: in-progress
depends: TASK-028, TASK-025
scope: .omi/agents/**, src/omi/template/dot-omi/agents/**, .omi/decisions.md
---
## Goal
The last two roles. Evaluation happens once, in TASK-039.

## Acceptance criteria
- [ ] `omi-agent-devops` (access write, sonnet, medium; haiku for mechanical config): CI, Docker, release scripts inside its task scope; default skills from the delivery-ops group; never touches secrets or pushes to `staging`/`main`.
- [ ] `omi-agent-docs-writer` (access write, haiku or sonnet, low): README, docs and changelog only, scope limited to docs paths.
- [ ] Each role states when to use / not use, output format, stop and escalate conditions, tools allowed and sources.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-032
