---
id: omi-skill-debug-root-cause
group: quality
description: Use when a test fails or behaviour is wrong, before any fix.
tokens: 289
tools: Read, Grep, Bash, Edit
source_repo: https://github.com/obra/superpowers
source_ref: v6.3.0
source_file: skills/systematic-debugging/SKILL.md
source_license: MIT
source_use: adapt
---
# Debug to the root cause

No fix before you can state the root cause and its evidence.

## When to use
- Failing test or wrong behaviour, especially after a failed fix.

## When not to use
- Compile errors that name the exact line.

## Inputs
- Error output, repro steps, code in scope, `git diff`.

## Steps
1. Reproduce it; if you cannot, gather data, don't guess.
2. Trace the bad value to its origin; fix there.
3. Grep every caller. State one hypothesis ("X is the cause because Y") and test it with one change.
4. Write a failing regression test, apply one fix at the shared point, run the suite.

## Outputs and evidence
- Root cause (file:line, why), failing-then-passing test, result.

## Stop and escalate
- Three failed fixes: BLOCKED. Cause outside the task: `NEEDS SCOPE`.

## Tools needed
- Read, Grep, Bash, Edit.
