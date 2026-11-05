---
id: omi-flow-feature-sensitive
summary: Feature touching auth, secrets, permissions, data, CI or the agent harness: architect design first, then implement, review, security review, automatic acceptance. Use only for that risk; plain feature is enough otherwise.
steps:
- id: plan | role: coordinator | skills: omi-skill-task-brief | input: PO idea | output: task file with scope and acceptance criteria | gate: none | stop: task file complete and PO picked it
- id: architect | role: omi-agent-architect | skills: | input: task file | output: options and one recommendation in the task file | gate: none | stop: recommendation recorded and trust boundaries named
- id: build | role: omi-agent-engineer | skills: omi-skill-lean-implementation | input: task file with recommendation | output: diff, tests passing, Checkpoint updated | gate: none | stop: every criterion has a passing test
- id: review | role: omi-agent-reviewer | skills: omi-skill-verify-evidence, omi-skill-simplify-review | input: task file, diff | output: VERDICT PASS or FAIL | gate: review | stop: VERDICT PASS
- id: security | role: omi-agent-security-reviewer | skills: omi-skill-diff-security-review, omi-skill-ci-workflow-audit, omi-skill-verify-evidence, omi-skill-simplify-review | input: task file, diff | output: findings with location and how verified, VERDICT | gate: review | stop: VERDICT PASS
- id: accept | role: coordinator | skills: | input: both PASS verdicts | output: `Auto accept: review PASS` line in ## Steps | gate: auto | stop: every review-type step passed or an explicit PO approval line
---
# Feature, sensitive

**When to use:** the diff can change who may do what, how secrets or personal data are handled, migrations, CI/workflows or the guard. Why not `omi-flow-feature`: no design check up front and no dedicated security review, so a boundary mistake is found late or not at all.
**Use instead:** `omi-flow-feature` when none of that applies.

## Models
- plan: Coordinator, sonnet/low.
- architect: architect, opus/high.
- build: engineer, sonnet/medium.
- review: reviewer, sonnet/medium, fresh each round.
- security: security-reviewer, sonnet/medium; opus/high when the diff touches auth, payment or secrets (AGENTS.md Quota rules).
- accept: Coordinator; automatic after review PASS.

## Review-fail rule
A FAIL at review or security goes back to build with the findings. Enforced in code: after `max_fix_rounds` (2) failed rounds `omi step <ID> back` and `omi run` refuse with `ROUND LIMIT` until the PO's words for this task and round are given (`--po "<words>"`, one more round; pick-list: rescope, change approach, drop). From round 2 a FAIL whose report ends `ROOT: same` makes `omi step back` return to architect (opus/high) to re-plan and prints `REPLAN: same root cause`.

## PO gates
`accept` is automatic: `omi step <ID> done` records `Auto accept: review PASS` under `## Steps` when every review-type step passed (or an explicit `PO approval accept:` line exists), and refuses otherwise. Merge to staging/main stays with the PO.
