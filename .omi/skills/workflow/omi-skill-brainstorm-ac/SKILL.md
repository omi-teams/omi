---
id: omi-skill-brainstorm-ac
group: workflow
description: Use when a requirement or feature request is vague and must become testable acceptance criteria before a task file is written.
tokens: 618
tools: Read, Write, Edit
source_repo: https://github.com/obra/superpowers
source_ref: v6.3.0
source_file: skills/brainstorming/SKILL.md
source_license: MIT
source_use: adapt
---
<!-- Adapted from Superpowers brainstorming (https://github.com/obra/superpowers) v6.3.0, MIT, Copyright (c) 2025 Jesse Vincent. Changes: reduced to the classify, ask, criteria loop. -->
# Brainstorm to acceptance criteria

Serves the Coordinator/architect step "split the backlog into TASK files" (`omi-idea` step 5). It works on one requirement at a time; the whole-product spec stays in `omi-idea`.

## When to use
- A request says "make it better", "support X" or similar, with no pass/fail test.
- Before writing `## Acceptance criteria` of a new `.omi/tasks/TASK-NNN.md`.

## When not to use
- The idea is a whole product with no `docs/product.md` yet: use `omi-idea`.
- The criteria are already testable: write the task directly.

## Inputs
- The raw requirement, `docs/product.md` if present, and the code it touches.

## Steps
1. Classify and say it aloud: spike (an answer, not kept code), bounded (the flow to change already exists in the repo), architectural (new subsystem or changed interfaces). When unsure take the heavier path; hidden complexity upgrades it, never downgrades.
2. Read the existing flow first; do not ask what the repo answers.
3. Ask the PO one question at a time, each with a suggested answer. Only ask about behaviour, limits, errors and out-of-scope.
4. For an architectural change, offer 2-3 approaches with trade-offs and a recommendation.
5. Write criteria as observable checks: given input, the visible result. Each names how it is verified (test, command, file). Replace words like "fast", "nice", "robust" with a number or an example.
6. Add one `Out of scope` line and list open questions as defaults you assumed.
7. Show the criteria to the PO and wait for an explicit yes before any task is created or run.

## Outputs and evidence
- A criteria list ready to paste into the task file, with the approval noted in the chat or `.omi/decisions.md`.

## Stop and escalate
- The PO cannot decide: record the assumption as a default and mark it clearly.
- The work needs more than one session: split it, one outcome per task.

## Tools needed
- Read, Write, Edit.
