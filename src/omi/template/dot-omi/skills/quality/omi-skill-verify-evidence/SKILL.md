---
id: omi-skill-verify-evidence
group: quality
description: Use when about to say work is done, fixed or passing, before reporting DONE, committing or approving a review.
tokens: 537
tools: Read, Bash
source_repo: https://github.com/obra/superpowers
source_ref: v6.3.0
source_file: skills/verification-before-completion/SKILL.md
source_license: MIT
source_use: adapt
---
<!-- Adapted from Superpowers verification-before-completion (https://github.com/obra/superpowers) v6.3.0, MIT, Copyright (c) 2025 Jesse Vincent. Changes: condensed; omi report format and reviewer use added. -->
# Verify with evidence

Rule: no success claim without a command run in this session whose output you read.

## When to use
- Before `DONE`, before a commit message says "fixes", before a reviewer approves.
- Before relaying another agent's "success": check the diff yourself.

## When not to use
- Pure questions or plans that claim nothing about the state of the code.

## Inputs
- The claim, the acceptance criteria, and the commands that can prove each one.

## Steps
1. For each claim, name the command that would prove it.
2. Run the full command fresh, not a subset or an earlier run. Read all output and the exit code; count failures.
3. Match the claim to the proof: tests pass = test run with 0 failures; build ok = build exit 0 (a linter is not a build); bug fixed = the original symptom no longer reproduces; criteria met = a line-by-line check against the task file, not "tests pass".
4. A new regression test must be seen failing without the fix, then passing with it.
5. If output contradicts the claim, report the real state with the output.
6. Words like "should", "probably", "looks right" mean you have not verified yet: run first.

## Outputs and evidence
- Per claim: command, result (exit code, pass/fail counts), and the criterion it covers. Untested items are listed as untested.

## Stop and escalate
- The command cannot run here (no tool, network or access): say so, mark the claim unverified, and report BLOCKED or NEEDS SCOPE.
- The same check fails three times: stop, report the output, do not claim success.

## Tools needed
- Read, Bash.
