---
id: omi-skill-task-brief
group: workflow
description: Use when a task file must be complete enough for a fresh engineer agent with zero context, before `omi run`.
tokens: 580
tools: Read, Write, Edit
source_repo: https://github.com/obra/superpowers
source_ref: v6.3.0
source_file: skills/writing-plans/SKILL.md
source_license: MIT
source_use: adapt
---
<!-- Adapted from Superpowers writing-plans (https://github.com/obra/superpowers) v6.3.0, MIT, Copyright (c) 2025 Jesse Vincent. Changes: shrunk from a full plan document to a short brief inside the task file. -->
# Task brief

Serves the Coordinator step before `omi run omi-agent-engineer <ID>` (`omi-task` step 3): the engineer sees only the task file and its worktree.

## When to use
- A task is `planned` and its Goal and criteria would not be clear to a stranger.
- A task failed review because the engineer guessed.

## When not to use
- Creating the backlog from an idea: use `omi-idea`.
- Changing the scope of a running task: use `omi-skill-change-request`.

## Inputs
- The task file from `.omi/tasks/_template.md`, the spec section it implements, and the files in its scope.

## Steps
1. Check size: one outcome, one session. If it covers independent parts, split it.
2. Goal: one or two sentences saying what exists afterwards, not how.
3. Under Goal add `### Brief` (at most 15 lines): files to create or change (exact paths), names and signatures it must keep or produce, how to run the tests, and the one pattern in the repo to copy.
4. Give constraints verbatim from the spec (versions, naming, limits) instead of paraphrasing.
5. Each acceptance criterion is a check the engineer can run or point to a test for.
6. No placeholders: "TBD", "handle edge cases", "similar to TASK-n" are failures; write the content.
7. Self-review: every spec requirement of this task maps to a criterion, and names match across tasks. Put the existing tests the change affects in `scope`. Set `scope` globs to the minimum, pick `role` and `skills` within the token budget.

## Outputs and evidence
- An updated task file with Goal, Brief, criteria, scope, role, skills; `python -m omi skills check <task-file>` passes.

## Stop and escalate
- The spec is ambiguous on behaviour: go back to `omi-skill-brainstorm-ac` or ask the PO.
- The needed scope is wider than the PO approved: ask for the decision.

## Tools needed
- Read, Write, Edit, Bash for the skills check.
