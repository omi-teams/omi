---
id: omi-flow-incident
summary: Respond to something broken after a release or gate: contain, diagnose the root cause, hotfix or rollback, then a postmortem note. Use when production, a release candidate, CI gate or ruleset broke; the production merge stays a PO gate.
steps:
- id: contain | role: coordinator | skills: omi-skill-incident | input: incident report, release and gate state | output: incident record with impact, start time and containment (freeze merges, pause workers) | gate: none | stop: damage stopped growing and the record exists
- id: diagnose | role: omi-agent-engineer | skills: omi-skill-debug-root-cause | input: incident record, logs, failing run | output: root cause with evidence and the choice hotfix or rollback | gate: none | stop: root cause named with evidence, or stop and ask the PO
- id: hotfix | role: omi-agent-engineer | skills: omi-skill-lean-implementation | input: root cause, task file, worktree | output: either the minimal fix with a regression test (tests passing) or the revert diff / previous rc redeploy plan if rollback was chosen | gate: review | stop: VERDICT PASS from a fresh reviewer
- id: merge-prod | role: coordinator | skills: omi-skill-rollback | input: reviewed hotfix or the bad promotion merge or rc tag | output: PO approval line in ## Steps, then hotfix merged or promotion reverted or previous rc redeployed | gate: po | stop: PO approved and service is healthy again
- id: postmortem | role: coordinator | skills: omi-skill-incident | input: incident record, root cause, actions taken | output: postmortem note with timeline, cause, fix and follow-up tasks, logged in decisions.md | gate: none | stop: note written and follow-ups are task files
---
# Incident

**When to use:** a release, CI gate, ruleset, tag or worker run broke and needs containing now. Why not `omi-flow-bugfix`: it has no containment, no rollback path and no postmortem, and it assumes time to review calmly.
**Use instead:** `omi-flow-bugfix` for a defect that hurts nobody yet; `omi-flow-feature-sensitive` for planned changes to CI or secrets.

## Models
- contain: Coordinator, sonnet/low.
- diagnose: engineer, sonnet/medium; opus/high if the cause is unknown after one attempt.
- hotfix: engineer, sonnet/medium; reviewer sonnet/medium, fresh instance each round.
- merge-prod: Coordinator prepares; the PO approves.
- postmortem: Coordinator, sonnet/low.

## Stop conditions
- Contain first: freeze merges and pause workers before any diagnosis.
- Rollback chosen: `hotfix` becomes the revert step (revert the promotion merge or redeploy the previous rc tag); it still goes through the review gate, never skipped, then `merge-prod` and `postmortem`.
- Root cause unknown after two attempts: stop and ask the PO (pick-list: rollback, keep investigating, accept the risk).
- A fix that needs files outside `scope`: report `NEEDS SCOPE`.

## Review-fail rule
Each FAIL goes back to hotfix with the findings. After 2 FAILs, prefer rollback over a third attempt and ask the PO (pick-list: rollback, rescope, change approach).

## PO gates
`merge-prod` needs `PO approval merge-prod: <PO's words>` under `## Steps`; `omi step` refuses otherwise. The production merge, revert or redeploy is never done without it.
