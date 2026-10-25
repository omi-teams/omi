---
id: TASK-035
title: Workflows - docs-only, spike
status: in-progress
depends: TASK-032, TASK-029, TASK-031
scope: .omi/workflows/**, src/omi/template/dot-omi/workflows/**, .omi/decisions.md
role: omi-agent-engineer
skills: []  # writes markdown workflows
---
## Goal
The two cheapest paths.

## Acceptance criteria
- [ ] `omi-flow-docs-only`: docs-writer then PO check; no reviewer (CI still runs), matching the quota rule.
- [ ] `omi-flow-spike`: researcher produces a cited report in `docs/`, no product code, ends in a PO decision.
- [ ] Each passes `--check`; catalog regenerated; template copy identical.
- [ ] docs-only uses the AGENTS.md path rule: reviewer skipped only when every changed path is under `docs/**`, `.omi/tasks/**` or is `.omi/decisions.md`; any other path (README.md, `.omi/agents`, `.omi/skills`, `.claude`, `src/omi/template`) switches to `omi-flow-feature`.
- [ ] spike: the researcher is read-only, so a write step (docs-writer) saves its cited report under `docs/`. Follow the layout of `.omi/workflows/omi-flow-feature.md`.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-036
