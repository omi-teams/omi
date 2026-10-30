---
id: TASK-126
title: omi board cost and quota view
status: planned
depends: TASK-125
plan: PLAN-007
scope: src/omi/board/**, tests/test_board.py, tests/test_board_web.py, .omi/tasks/TASK-126-mockup/**, .omi/tasks/TASK-126.md
role: omi-agent-engineer
skills: [omi-skill-ui-direction]
refs: []
tool:
model:
effort:
step_settings:
workflow: omi-flow-feature-ui
step:
---
## Goal
The PO sees where tokens and money go: usage per task, plan, tool and model, review rounds, and the most expensive tasks.

## Acceptance criteria
- [ ] A mockup in `.omi/tasks/TASK-126-mockup/` is PO-approved before build.
- [ ] The API sums the `## Usage` tables (in, out, cache tokens, runs) per task, plan, tool and model, plus review rounds per task.
- [ ] A cost estimate in USD is shown only when `.omi/config.json` has a `prices` map per model; otherwise tokens only, labelled as such.
- [ ] Top 5 most expensive tasks and tasks with 2+ review FAILs are highlighted; bars use the dataviz rules (not colour alone).
- [ ] Tests cover the sums on a fixture with mixed tools and a missing `prices` map.
- [ ] The board stays read-only; state text via `textContent` only; no external script, font or CDN; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
