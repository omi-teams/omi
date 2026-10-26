---
id: omi-flow-docs-only
summary: Documentation-only change: docs-writer, then PO check; no reviewer (CI still runs). Use only when every changed path is under docs/**, .omi/tasks/** or is .omi/decisions.md; any other path needs feature.
steps:
- id: plan | role: coordinator | skills: omi-skill-task-brief | input: PO request | output: task file whose scope lists only docs/**, .omi/tasks/** or .omi/decisions.md | gate: none | stop: task file complete and PO picked it
- id: write | role: omi-agent-docs-writer | skills: | input: task file, worktree | output: docs diff inside scope, Checkpoint updated | gate: none | stop: every criterion met; no path outside the allowed list changed
- id: accept | role: coordinator | skills: | input: diff summary, CI result | output: PO approval line in ## Steps | gate: po | stop: PO accepts the result
---
# Docs only

**When to use:** the change touches only `docs/**`, `.omi/tasks/**` or `.omi/decisions.md`. Then the reviewer is skipped (quota rule); CI still runs.
**Use instead:** `omi-flow-feature` as soon as any other path changes: `README.md`, `.omi/agents`, `.omi/skills`, `.claude`, `src/omi/template` or anything else. Those carry behaviour and get an independent review.

## Models
- plan: Coordinator, sonnet/low.
- write: docs-writer, sonnet/low.
- accept: Coordinator; the PO decides.

## Path rule
Before `accept`, list the changed paths. Reviewer skipped only when every path is under `docs/**`, `.omi/tasks/**` or is `.omi/decisions.md`. If one is not, stop and restart the task on `omi-flow-feature`.

## Stop conditions
- A needed edit outside the allowed paths: stop and report `NEEDS SCOPE`; switch to `omi-flow-feature`.
- CI red: fix before `accept`.

## PO gates
`accept` needs `PO approval accept: <PO's words>` under `## Steps`; `omi step` refuses otherwise. Merge to staging/main stays with the PO.
