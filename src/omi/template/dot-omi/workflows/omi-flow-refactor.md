---
id: omi-flow-refactor
summary: Restructure code without changing behaviour: tests green before, change, tests green after, independent simplify review, automatic acceptance on review PASS. Use when behaviour must stay identical; use bugfix or feature if behaviour changes.
steps:
- id: plan | role: coordinator | skills: omi-skill-task-brief | input: PO request | output: task file with the structural goal, a tight scope and the behaviour that must not change | gate: none | stop: task file complete and PO picked it
- id: baseline | role: omi-agent-engineer | skills: omi-skill-lean-implementation | input: task file, worktree | output: test result before any change, missing characterization tests added, Checkpoint updated | gate: none | stop: tests green before the refactor; if red, stop and report
- id: refactor | role: omi-agent-engineer | skills: omi-skill-lean-implementation | input: task file, green baseline | output: diff inside scope, tests green after, no test edited to pass | gate: none | stop: tests green and behaviour unchanged; scope not grown
- id: review | role: omi-agent-reviewer | skills: omi-skill-simplify-review | input: task file, diff | output: VERDICT PASS or FAIL | gate: review | stop: VERDICT PASS
- id: accept | role: coordinator | skills: | input: PASS verdict, diff summary | output: `Auto accept: review PASS` line in ## Steps | gate: auto | stop: every review-type step passed or an explicit PO approval line
---
# Refactor

**When to use:** structure, naming or duplication changes where observable behaviour must stay identical. Why not `omi-flow-feature`: it has no before/after test proof and no guard against scope growth.
**Use instead:** `omi-flow-bugfix` when a defect is fixed; `omi-flow-feature` when behaviour changes.

## Models
- plan: Coordinator, sonnet/low.
- baseline: engineer, sonnet/low.
- refactor: engineer, sonnet/medium.
- review: reviewer, sonnet/medium, fresh instance each round.
- accept: Coordinator; automatic after review PASS.

## Stop conditions
- Tests red before the change: stop; fixing them is a separate bugfix task.
- A behaviour change or a needed edit outside `scope` appears: stop and report (`NEEDS SCOPE`), no scope growth.
- A test must be changed to pass: stop and ask the PO; behaviour is not unchanged.

## Review-fail rule
Each FAIL goes back to refactor with the findings. Enforced in code: after `max_fix_rounds` (2) failed rounds `omi step <ID> back` and `omi run` refuse with `ROUND LIMIT` until the PO's words for this task and round are given (`--po "<words>"`, one more round; pick-list: rescope, change approach, drop). From round 2 a FAIL whose report ends `ROOT: same` prints `REPLAN: same root cause`; this workflow has no architect step, so `back` needs `--po`.

## PO gates
`accept` is automatic: `omi step <ID> done` records `Auto accept: review PASS` under `## Steps` when every review-type step passed (or an explicit `PO approval accept:` line exists), and refuses otherwise. Use `omi-flow-feature-sensitive` (PO gate) for security-sensitive work. Merge to staging/main stays with the PO.
