---
id: lean-implementation
group: workflow
description: Use when writing or fixing code and tempted to add abstractions, dependencies or config; keeps the diff minimal (YAGNI, stdlib first).
tokens: 571
tools: Read, Edit, Bash
source_repo: https://github.com/DietrichGebert/ponytail
source_ref: v4.10.0
source_file: ponytail.md
source_license: MIT
source_use: adapt
---
<!-- Adapted from Ponytail (https://github.com/DietrichGebert/ponytail) v4.10.0, MIT, Copyright (c) 2026 DietrichGebert. Changes: dropped modes and persona, kept the ladder and rules. -->
# Lean implementation

Serves the engineer step "cover each criterion with a test, then run the tests" (`.omi/agents/engineer.md` step 3).

## When to use
- Any code change in a task, before writing the first line.

## When not to use
- Never lean away: input validation at trust boundaries, data-loss error handling, security, accessibility basics, anything the criteria require.

## Inputs
- The task file, the code in scope, and its tests.

## Steps
1. Read the task and trace the real flow end to end first; the ladder shortens the solution, never the reading.
2. Climb and stop at the first rung that holds: needed at all (else skip and say so)? already in this repo (reuse)? standard library? native platform feature? dependency already installed? one line? only then the minimum code.
3. Do not add a new dependency for what a few lines do.
4. No interface with one implementation, no factory for one product, no config for a constant, no scaffolding "for later".
5. Bug fix: grep every caller, fix once at the shared point (root cause, not symptom).
6. Prefer deleting code over adding it; fewest files, shortest correct diff. Between equal options take the one correct on edge cases.
7. Mark a deliberate corner cut with a comment naming the ceiling, e.g. `# ponytail: global lock, per-key if contention`.
8. Non-trivial logic leaves one small runnable test; trivial one-liners need none.

## Outputs and evidence
- A small diff inside scope, passing tests, and in the report at most three lines on what was skipped and when to add it.

## Stop and escalate
- The lean solution does not meet a criterion, or needs files the task does not list: report `NEEDS SCOPE`.

## Tools needed
- Read, Edit, Bash for tests.
