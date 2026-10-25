---
id: omi-flow-feature-sensitive
summary: Feature touching auth, secrets, permissions, data, CI or the agent harness: architect design first, then implement, review, security review, PO acceptance. Use only for that risk; plain feature is enough otherwise.
steps:
- id: plan | role: coordinator | skills: omi-skill-task-brief | input: PO idea | output: task file with scope and acceptance criteria | gate: none | stop: task file complete and PO picked it
- id: architect | role: omi-agent-architect | skills: | input: task file | output: options and one recommendation in the task file | gate: none | stop: recommendation recorded and trust boundaries named
- id: build | role: omi-agent-engineer | skills: omi-skill-lean-implementation | input: task file with recommendation | output: diff, tests passing, Checkpoint updated | gate: none | stop: every criterion has a passing test
- id: review | role: omi-agent-reviewer | skills: | input: task file, diff | output: VERDICT PASS or FAIL | gate: review | stop: VERDICT PASS
- id: security | role: omi-agent-security-reviewer | skills: omi-skill-diff-security-review | input: task file, diff | output: findings with location and how verified, VERDICT | gate: review | stop: VERDICT PASS
- id: accept | role: coordinator | skills: | input: both PASS verdicts | output: PO approval line in ## Steps | gate: po | stop: PO accepts the result
---
# Feature, sensitive

**When to use:** the diff can change who may do what, how secrets or personal data are handled, migrations, CI/workflows or the guard. Why not `omi-flow-feature`: no design check up front and no dedicated security review, so a boundary mistake is found late or not at all.
**Use instead:** `omi-flow-feature` when none of that applies.

## Models
- plan: Coordinator, sonnet/low.
- architect: architect, opus/high.
- build: engineer, sonnet/medium.
- review: reviewer, sonnet/medium, fresh each round.
- security: security-reviewer, sonnet/medium.
- accept: Coordinator; the PO decides.

## Review-fail rule
A FAIL at review or security goes back to build with the findings. After 2 FAILs, escalate: architect (opus/high) re-plans, or the engineer runs on opus. A third FAIL: stop and ask the PO (rescope, change approach, drop).

## PO gates
`accept` needs `PO approval accept: <PO's words>` under `## Steps`. Merge to staging/main stays with the PO.
