---
id: omi-flow-bugfix-fast
summary: Fast lane for a small bug: reproduce and fix in one engineer run, one review run that also walks the security checklist, automatic acceptance, merge on green CI. Use only for a bug touching at most 3 non-test files outside sensitive scope (auth, secrets, migrations, CI); otherwise bugfix or feature-sensitive.
steps:
- id: plan | role: coordinator | skills: omi-skill-task-brief | input: PO bug report | output: task file with symptom, expected behaviour, scope of at most 3 non-test files and acceptance criteria | gate: none | stop: task file complete
- id: reproduce-fix | role: omi-agent-engineer | skills: omi-skill-lean-implementation, omi-skill-debug-root-cause | input: task file, worktree | output: failing test first, then the root-cause fix; the report has `Reproduced: <test> failed before the fix` | gate: none | stop: reproducing test passes and the changed modules' tests are green
- id: review | role: omi-agent-reviewer | skills: omi-skill-verify-evidence, omi-skill-simplify-review, omi-skill-diff-security-review | input: task file, diff | output: VERDICT PASS or FAIL, covering the security checklist too | gate: review | stop: VERDICT PASS
- id: accept | role: coordinator | skills: | input: PASS verdict | output: `Auto accept: review PASS` line in ## Steps | gate: auto | stop: review passed; `omi advance` merges on green CI
---
# Bugfix, fast lane

**When to use:** a bug with a reproducible symptom whose fix touches at most 3 non-test files, none under auth, secrets, migrations or CI. One engineer run reproduces and fixes, one reviewer run checks correctness and the security checklist.
**Use instead:** `omi-flow-bugfix` when the cause is unknown or the fix is larger; `omi-flow-feature-sensitive` for sensitive scope. `omi step` warns when a small bug takes `omi-flow-bugfix` and when sensitive scope takes this lane.

## Models
- plan: Coordinator, sonnet/low.
- reproduce-fix: engineer; `omi dispatch` picks the role's `small:` setting for at most 3 non-test files.
- review: reviewer, fresh instance each round.
- accept: Coordinator; automatic after review PASS.

## Stop conditions
- Cannot reproduce, or the fix needs more than 3 non-test files: stop; the Coordinator moves the task to `omi-flow-bugfix`.
- Root cause outside `scope`: report `NEEDS SCOPE`.

## Review-fail rule
Each FAIL goes back to reproduce-fix with the findings. After `max_fix_rounds` (2) failed rounds `omi step <ID> back` and `omi run` refuse with `ROUND LIMIT` until the Coordinator decides.

## PO gates
None: `accept` is automatic and `omi advance` merges to development on green CI. Merge to staging/main stays with the PO.
