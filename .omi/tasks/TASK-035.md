---
id: TASK-035
title: Workflows - docs-only, spike
status: done
depends: TASK-032, TASK-029, TASK-031
scope: .omi/workflows/**, src/omi/template/dot-omi/workflows/**, .omi/decisions.md
role: omi-agent-engineer
skills: []  # writes markdown workflows
---
## Goal
The two cheapest paths.

## Acceptance criteria
- [x] `omi-flow-docs-only`: docs-writer then PO check; no reviewer (CI still runs), matching the quota rule.
- [x] `omi-flow-spike`: researcher produces a cited report in `docs/`, no product code, ends in a PO decision.
- [x] Each passes `--check`; catalog regenerated; template copy identical.
- [x] docs-only uses the AGENTS.md path rule: reviewer skipped only when every changed path is under `docs/**`, `.omi/tasks/**` or is `.omi/decisions.md`; any other path (README.md, `.omi/agents`, `.omi/skills`, `.claude`, `src/omi/template`) switches to `omi-flow-feature`.
- [x] spike: the researcher is read-only, so a write step (docs-writer) saves its cited report under `docs/`. Follow the layout of `.omi/workflows/omi-flow-feature.md`.

## Checkpoint
Done: all AC; omi-flow-docs-only and omi-flow-spike, template copies, catalog regenerated.
Not done: -
Tests: workflows --check ok (7 checked); template identical.
Next: TASK-036

## Usage
| role | model | effort | input | output | cache | duration | skills read |
|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 14 | 3061 | 150263 | 37s | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 12 | 1669 | 148530 | 35s | - |
