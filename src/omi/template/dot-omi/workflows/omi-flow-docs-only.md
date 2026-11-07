---
id: omi-flow-docs-only
summary: Documentation-only change: docs-writer, reviewer, then automatic accept (CI still runs). Use only when every changed path is under docs/**, .omi/tasks/** or is .omi/decisions.md; any other path needs feature.
steps:
- id: plan | role: coordinator | skills: omi-skill-task-brief | input: PO request | output: task file whose scope lists only docs/**, .omi/tasks/** or .omi/decisions.md | gate: none | stop: task file complete and PO picked it
- id: write | role: omi-agent-docs-writer | skills: omi-skill-verify-evidence | input: task file, worktree | output: docs diff inside scope, Checkpoint updated | gate: none | stop: every criterion met; no path outside the allowed list changed
- id: review | role: omi-agent-reviewer | skills: omi-skill-verify-evidence | input: task file, diff | output: VERDICT PASS or FAIL | gate: review | stop: VERDICT PASS
- id: accept | role: coordinator | skills: | input: PASS verdict, diff summary, CI result | output: `Auto accept: review PASS` line in ## Steps | gate: auto | stop: every review-type step passed or an explicit PO approval line
---
# Docs only

**When to use:** the change touches only `docs/**`, `.omi/tasks/**` or `.omi/decisions.md`. The reviewer still checks the docs diff; CI still runs.
**Use instead:** `omi-flow-feature` as soon as any other path changes: `README.md`, `.omi/agents`, `.omi/skills`, `.claude`, `src/omi/template` or anything else. Those carry behaviour and get an independent review.

## Models
- plan: Coordinator, sonnet/low.
- write: docs-writer, sonnet/low.
- review: reviewer, sonnet/low, fresh instance each round.
- accept: Coordinator; automatic after review PASS.

## Path rule
Before `review`, list the changed paths. This workflow applies only when every path is under `docs/**`, `.omi/tasks/**` or is `.omi/decisions.md`. If one is not, stop and restart the task on `omi-flow-feature`.

## Stop conditions
- A needed edit outside the allowed paths: stop and report `NEEDS SCOPE`; switch to `omi-flow-feature`.
- CI red: fix before `accept`.

## PO gates
`accept` is automatic: `omi step <ID> done` records `Auto accept: review PASS` under `## Steps` when every review-type step passed (or an explicit `PO approval accept:` line exists), and refuses otherwise. Merge to staging/main stays with the PO.
