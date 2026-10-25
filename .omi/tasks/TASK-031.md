---
id: TASK-031
title: Roles - delivery (devops, docs-writer)
status: done
depends: TASK-028, TASK-025
scope: .omi/agents/**, src/omi/template/dot-omi/agents/**, .omi/decisions.md
---
## Goal
The last two roles. Evaluation happens once, in TASK-039.

## Acceptance criteria
- [x] `omi-agent-devops` (access write, sonnet, medium; haiku for mechanical config): CI, Docker, release scripts inside its task scope; default skills from the delivery-ops group; never touches secrets or pushes to `staging`/`main`.
- [x] `omi-agent-docs-writer` (access write, haiku or sonnet, low): README, docs and changelog only, scope limited to docs paths.
- [x] Each role states when to use / not use, output format, stop and escalate conditions, tools allowed and sources.

## Checkpoint
Done: omi-agent-devops (write, sonnet/medium, haiku for mechanical config; skills release-checklist, docker-worker-pitfalls, windows-powershell) and omi-agent-docs-writer (write, haiku/low, README, docs/**, changelog); catalog regenerated (9 roles); template copy identical.
Not done: -
Tests: tests/test_omi.py ok; skills check ok with role omi-agent-devops.
Next: TASK-032
