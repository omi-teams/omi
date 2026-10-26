---
id: omi-skill-change-request
group: workflow
description: Use when requirements, scope or an approved decision change after a task started, or an engineer reports NEEDS SCOPE.
tokens: 520
tools: Read, Write, Edit
source_repo: https://github.com/bmad-code-org/BMAD-METHOD
source_ref: 61e01f8
source_file: README.md
source_license: MIT
source_use: reference
---
<!-- Reference only: BMAD (MIT, Copyright (c) 2025 BMad Code, LLC), README at 61e01f8, idea of a change request that loops back to planning. Text written fresh. -->
# Change request

Serves the Coordinator step in `omi-task` step 5 when the engineer returns `NEEDS SCOPE`, and any PO request that alters approved work.

## When to use
- The PO or reviewer asks for something outside the task's Goal or criteria.
- `NEEDS SCOPE` names paths the task does not cover.
- A decision in `.omi/decisions.md` or `docs/product.md` no longer holds.

## When not to use
- A fix inside existing criteria: that is a normal review round.
- A brand-new feature: create a task via `omi-idea` or `omi-skill-brainstorm-ac`.

## Inputs
- The task file, the change in one sentence, and the diff so far.

## Steps
1. Stop the engineer; do not let it continue on assumptions. Keep the work done so far.
2. Write the impact in at most 5 lines: criteria that change, files or scope added, tasks that depend on it, extra cost.
3. Pick one option: (a) widen this task, (b) new follow-up task and keep this one as is, (c) drop the change. Recommend one.
4. Ask the PO to choose from those options, recommended first. Only the PO widens scope or edits approved criteria.
5. On the answer: append to `.omi/decisions.md` `- <date> | <decision> | <why> | <TASK-ID>`; edit the task file (scope, criteria, Checkpoint) and commit it on `development`.
6. Rerun `omi run` or create the new task through `omi-skill-task-brief`.

## Outputs and evidence
- A decisions line, an updated task file, and a commit sha.

## Stop and escalate
- The PO is unavailable: leave the task `in-progress`, note the open question in Checkpoint, change nothing.

## Tools needed
- Read, Write, Edit.
