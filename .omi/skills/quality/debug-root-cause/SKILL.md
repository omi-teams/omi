---
id: debug-root-cause
group: quality
description: Use when a test fails, a bug or unexpected behaviour appears, or a first fix did not work, before proposing any fix.
tokens: 588
tools: Read, Grep, Bash, Edit
source_repo: https://github.com/obra/superpowers
source_ref: v6.3.0
source_file: skills/systematic-debugging/SKILL.md
source_license: MIT
source_use: adapt
---
<!-- Adapted from Superpowers systematic-debugging (https://github.com/obra/superpowers) v6.3.0, MIT, Copyright (c) 2025 Jesse Vincent. Changes: condensed to four phases, omi escalation added. -->
# Debug to the root cause

Rule: no fix before you can state the root cause and the evidence for it.

## When to use
- Any failing test, build error or wrong behaviour; especially under time pressure or after a failed fix.

## When not to use
- Typos and compile errors whose message names the exact line and cause.

## Inputs
- The error output, the steps to reproduce, the code in scope and recent changes (`git log`, `git diff`).

## Steps
1. Read the whole error and stack trace. Reproduce it reliably; if you cannot, gather more data instead of guessing.
2. Check what changed recently: diff, dependencies, config, environment.
3. Across several components, log or print what enters and leaves each boundary, run once, and find the layer where the data goes wrong.
4. Trace the bad value backwards to where it originates; fix there, not where it shows up.
5. Compare with similar working code and list every difference.
6. Write one hypothesis: "X is the cause because Y". Change one thing to test it. Wrong: form a new hypothesis, do not stack fixes.
7. Write a failing test that reproduces the bug, apply a single fix, then run the test and the full suite.
8. Count fix attempts. After three failed fixes, stop: the design may be wrong.

## Outputs and evidence
- Root cause (file:line and why), the reproduction, the failing-then-passing test, and the full test result.
- If it is environmental or external: what you checked, and the handling added (retry, message).

## Stop and escalate
- Three fixes failed, or each fix reveals a new problem elsewhere: report BLOCKED with findings; ask for an architecture decision.
- The cause lies in files the task does not list: report `NEEDS SCOPE`.

## Tools needed
- Read, Grep, Bash for reproduction and tests, Edit for the fix.
