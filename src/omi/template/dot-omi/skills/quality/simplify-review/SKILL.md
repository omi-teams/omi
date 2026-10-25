---
id: simplify-review
group: quality
description: Use when reviewing a diff for over-engineering, needless dependencies or speculative abstractions; lists what to cut.
tokens: 547
tools: Read, Grep, Bash
source_repo: https://github.com/DietrichGebert/ponytail
source_ref: v4.10.0
source_file: skills/ponytail-review/SKILL.md, skills/ponytail-audit/SKILL.md
source_license: MIT
source_use: adapt
---
<!-- Adapted from Ponytail ponytail-review and ponytail-audit (https://github.com/DietrichGebert/ponytail) v4.10.0, MIT, Copyright (c) 2026 DietrichGebert. Changes: evidence and escalation sections added; diff only. -->
# Simplify review

Reads a diff and lists what can be cut. It does not apply changes.

## When to use
- Reviewing a diff for needless complexity before approval.

## When not to use
- Correctness, security or performance defects: report those through the normal review. A small smoke test or assert-based self-check is never bloat.

## Inputs
- The diff, the task file with its criteria, and the repo for reuse checks.

## Steps
1. Read the diff against the criteria; anything no criterion needs is a candidate.
2. For each candidate, search the repo and stdlib to confirm the replacement exists (grep the callers, check the function name).
3. One line per finding: `file:Lstart-end: tag what. replacement.` Tags: `delete` (dead or speculative code), `stdlib` (name the function), `native` (name the platform feature), `yagni` (one implementation, unused config, one-caller layer), `shrink` (same logic, shorter form shown).
4. Add `verified:` to each line: what you grepped or ran to confirm it is unused or replaceable.
5. End with `net: -N lines possible`. Nothing to cut: `Lean already.`

## Outputs and evidence
- A list with location, reason (tag and why) and verification for every line. Findings without verification are marked `unverified`.

## Stop and escalate
- A cut would change behaviour a criterion requires, or touches files outside the diff: do not list it as safe; flag it for the Coordinator.
- More than 15 findings: report the top 10 by lines saved and ask whether to continue.

## Tools needed
- Read, Grep, Bash (read-only commands, tests).
