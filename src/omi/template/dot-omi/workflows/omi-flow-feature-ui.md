---
id: omi-flow-feature-ui
summary: Feature with a UI change: UI spec first, then implement, review, browser QA with screenshots, PO acceptance. Use when screens or interaction change; plain feature is enough for backend or non-visual work.
steps:
- id: plan | role: coordinator | skills: omi-skill-task-brief | input: PO idea | output: task file with scope and acceptance criteria | gate: none | stop: task file complete and PO picked it
- id: design | role: omi-agent-designer-ui | skills: omi-skill-ui-direction | input: task file | output: UI spec in the task file | gate: none | stop: spec covers states, a11y and layout
- id: build | role: omi-agent-engineer | skills: omi-skill-lean-implementation | input: task file with UI spec | output: diff, tests passing, Checkpoint updated | gate: none | stop: every criterion has a passing test
- id: review | role: omi-agent-reviewer | skills: | input: task file, diff | output: VERDICT PASS or FAIL | gate: review | stop: VERDICT PASS
- id: qa | role: omi-agent-qa-tester | skills: omi-skill-web-qa | input: task file, running build | output: pass/fail per criterion with screenshots | gate: review | stop: all criteria pass
- id: accept | role: coordinator | skills: | input: PASS verdict, QA report | output: PO approval line in ## Steps | gate: po | stop: PO accepts the result
---
# Feature with UI

**When to use:** the change alters what a user sees or does. Why not `omi-flow-feature`: it has no design spec and no browser check, so layout, a11y and visual regressions slip through.
**Use instead:** `omi-flow-feature-sensitive` if it also touches auth, data or secrets (run it, and ask the PO to add design and QA).

## Models
- plan: Coordinator, sonnet/low.
- design: designer-ui, sonnet/medium.
- build: engineer, sonnet/medium.
- review: reviewer, sonnet/medium, fresh each round.
- qa: qa-tester, sonnet/medium.
- accept: Coordinator; the PO decides.

## Review-fail rule
A FAIL at review or qa goes back to build with the findings. After 2 FAILs, bring in the architect (opus/high) or switch the engineer to opus. A third FAIL: stop and ask the PO (rescope, change approach, drop).

## PO gates
`accept` needs `PO approval accept: <PO's words>` under `## Steps`. Merge to staging/main stays with the PO.
