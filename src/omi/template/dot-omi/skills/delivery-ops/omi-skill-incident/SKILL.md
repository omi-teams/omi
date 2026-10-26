---
id: omi-skill-incident
group: delivery-ops
description: Use when something broke in a release, CI gate, ruleset, tag or worker run and you must triage, contain and record it.
tokens: 534
tools: Read, Bash
source_repo: https://github.com/omi-teams/omi-squad2
source_ref: a35ba0957a0a8e7e431fbbaba2b3df1f3588a79d
source_file: docs/pilot.md, .omi/tasks/TASK-018.md, .omi/tasks/TASK-010.md, .omi/decisions.md
source_license: internal (no LICENSE file yet)
source_use: rewrite
---
# Incident

Worked example: pilot problem 6 (`docs/pilot.md`). The ruleset required a check `test` that never appeared, so the gate could not pass and the PO bypassed it. TASK-018 fixed the cause.

## When to use
- A gate fails for no code reason, a tag or ruleset is wrong, a release misbehaves, or a worker run leaves a mess.

## When not to use
- An ordinary failing test in a task: use `omi-skill-debug-root-cause`.

## Inputs
- The symptom, the exact command and output, the time, and what changed last (`git log`, last CI run).

## Steps
1. Contain first: stop further merges and promotions; if the release is bad, follow `omi-skill-rollback`. Do not bypass a gate to "get through" unless the PO decides.
2. Reproduce with one command and keep its output.
3. Separate cause from symptom: ask what the check or rule actually matched (the pilot gate required a name the matrix never emitted), not only that it was red.
4. Fix the cause in a task with a regression test (TASK-018 added tests for check-name discovery and, after review, for a `404` hidden in a sha or repo name).
5. Record: a row in `docs/pilot.md`-style "problem / fix / task" form, and a line in `.omi/decisions.md` when a rule changes.
6. Any bypass that did happen is written down with who approved it.

## Outputs and evidence
- Symptom with command output, root cause, fix task ID, test proving it, decision line if a rule changed.

## Stop and escalate
- Credentials, tokens or PO account actions are involved: stop and tell the PO (decisions: the PO account is not kept logged in on the squad machine).
- The fix needs a ruleset or tag change: the PO runs `omi github`; stop.

## Tools needed
- Read, Bash.
