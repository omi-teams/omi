---
id: omi-flow-bugfix
summary: Fix a defect at its root cause: failing test first, root-cause fix across all callers, regression test, independent review, automatic acceptance on review PASS. Use for a reported bug with a reproducible symptom; use feature for new behaviour.
steps:
- id: plan | role: coordinator | skills: omi-skill-task-brief | input: PO bug report | output: task file with symptom, expected behaviour, scope and acceptance criteria | gate: none | stop: task file complete and PO picked it
- id: reproduce | role: omi-agent-engineer | skills: omi-skill-lean-implementation, omi-skill-debug-root-cause | input: task file, worktree | output: failing test that shows the symptom, Checkpoint updated | gate: none | stop: test fails for the reported reason; if it cannot be reproduced, stop and report
- id: fix | role: omi-agent-engineer | skills: omi-skill-debug-root-cause | input: task file, failing test | output: root-cause fix after grep of all callers, regression test, diff, tests passing | gate: none | stop: reproducing test passes, full suite green, no symptom-only patch
- id: review | role: omi-agent-reviewer | skills: omi-skill-verify-evidence, omi-skill-simplify-review | input: task file, diff | output: VERDICT PASS or FAIL | gate: review | stop: VERDICT PASS
- id: accept | role: coordinator | skills: | input: PASS verdict, diff summary | output: `Auto accept: review PASS` line in ## Steps | gate: auto | stop: every review-type step passed or an explicit PO approval line
---
# Bugfix

**When to use:** a defect with a reproducible symptom in existing code. Why not `omi-flow-feature`: it has no reproduce-first step and no root-cause discipline, so a symptom patch can pass review.
**Use instead:** `omi-flow-feature` for new behaviour; `omi-flow-feature-sensitive` if the fix touches auth, secrets, data or CI; `omi-flow-refactor` when behaviour must not change.

## Models
- plan: Coordinator, sonnet/low.
- reproduce: engineer, sonnet/medium.
- fix: engineer, sonnet/medium; opus/high if the cause is still unknown after one attempt.
- review: reviewer, sonnet/medium, fresh instance each round.
- accept: Coordinator; automatic after review PASS.

## Stop conditions
- Cannot reproduce: stop and ask the PO for more detail (pick-list: provide steps, drop).
- Root cause lies outside `scope`: report `NEEDS SCOPE`, do not patch the symptom inside scope.
- Fix needs a behaviour change beyond the report: stop and ask the PO.

## Review-fail rule
Each FAIL goes back to fix with the findings. Enforced in code: after `max_fix_rounds` (2) failed rounds `omi step <ID> back` and `omi run` refuse with `ROUND LIMIT` until the PO's words for this task and round are given (`--po "<words>"`, one more round; pick-list: rescope, change approach, drop). From round 2 a FAIL whose report ends `ROOT: same` prints `REPLAN: same root cause`; this workflow has no architect step, so `back` needs `--po`.

## PO gates
`accept` is automatic: `omi step <ID> done` records `Auto accept: review PASS` under `## Steps` when every review-type step passed (or an explicit `PO approval accept:` line exists), and refuses otherwise. Use `omi-flow-feature-sensitive` for security-sensitive work. Merge to staging/main stays with the PO.
