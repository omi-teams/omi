---
id: omi-flow-feature
summary: Default build path for one product change: plan, implement, independent review, automatic acceptance on review PASS. Use for any normal feature or fix; use feature-ui if the UI changes, feature-sensitive for auth, secrets, data or CI.
steps:
- id: plan | role: coordinator | skills: omi-skill-task-brief | input: PO idea | output: task file with scope and acceptance criteria | gate: none | stop: task file complete and PO picked it
- id: build | role: omi-agent-engineer | skills: omi-skill-lean-implementation | input: task file, worktree | output: diff, tests passing, Checkpoint updated | gate: none | stop: every criterion has a passing test
- id: review | role: omi-agent-reviewer | skills: | input: task file, diff | output: VERDICT PASS or FAIL | gate: review | stop: VERDICT PASS
- id: accept | role: coordinator | skills: | input: PASS verdict, diff summary | output: `Auto accept: review PASS` line in ## Steps | gate: auto | stop: last review-type step passed
---
# Feature

**When to use:** the default for one product change with clear acceptance criteria. It is the lightest build path; docs-only edits follow the reviewer skip rule.
**Use instead:** `omi-flow-feature-ui` when screens change (needs a design spec and a browser check); `omi-flow-feature-sensitive` when the change touches auth, secrets, permissions, data/migrations, CI or the agent harness.

## Models
- plan: Coordinator, sonnet/low.
- build: engineer, sonnet/medium.
- review: reviewer, sonnet/medium, fresh instance each round.
- accept: Coordinator; automatic after review PASS.

## Review-fail rule
Each FAIL goes back to build with the findings. After 2 FAILs, run the next build with the architect (opus/high) advising, or switch the engineer to opus. A third FAIL: stop and ask the PO (pick-list: rescope, change approach, drop).

## PO gates
`accept` is automatic: `omi step <ID> done` records `Auto accept: review PASS` under `## Steps` when the last review-type step passed, and refuses otherwise. Use `omi-flow-feature-sensitive` (PO gate) for security-sensitive work. Merge to staging/main stays with the PO.
