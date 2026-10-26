---
id: omi-skill-debug-root-cause
group: quality
description: Use when a test fails or behaviour is wrong, before fixing.
tokens: 294
tools: Read, Grep, Bash, Edit
source_repo: https://github.com/obra/superpowers
source_ref: v6.3.0
source_file: skills/systematic-debugging/SKILL.md
source_license: MIT
source_use: adapt
---
<!-- Adapted from obra/superpowers systematic-debugging v6.3.0, MIT, Copyright (c) 2025 Jesse Vincent. -->
# Debug to the root cause

No fix before you can state the root cause and its evidence.

## When to use
- Failing test or wrong behaviour, esp. after a failed fix.

## When not to use
- Compile errors naming the exact line.

## Inputs
- Error output, repro steps.

## Steps
1. Reproduce it; if not, gather data, don't guess.
2. Trace the bad value to its origin; fix there.
3. Grep every caller. Hypothesis ("X causes Y"), tested with one change.
4. Write a failing regression test, fix once at the shared point, run suite.

## Outputs and evidence
- Root cause (file:line, why), failing-then-passing test.

## Stop and escalate
- Three failed fixes: BLOCKED. Cause outside the task: `NEEDS SCOPE`.

## Tools needed
- Read, Grep, Bash, Edit.
