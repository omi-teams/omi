---
id: omi-skill-issue-types
group: workflow
description: Use when filing any issue or task: which type, where it sits in the tree, which workflow, where to log it and the body shape per type.
tokens: 1200
tools: Read, Write, Edit
source_repo: https://github.com/omi-teams/omi
source_ref: v0.5.0
source_file: docs/product.md
source_license: MIT
source_use: rewrite
---
# Issue types

Serves the Coordinator and any agent filing an issue: `omi-idea` step 5, `omi-task` step 5 (`FOUND:`) and `omi-skill-task-brief`. `tasks.tree_errors` enforces the tree table.

## When to use
- Creating a task file, or reporting a `FOUND:`; choose `type`, `parent`, `workflow`, `role` first.

## When not to use
- Changing an existing task's scope: `omi-skill-change-request`.

## Inputs
- The finding or request, `docs/product.md`, and the existing tasks in `.omi/tasks/`.

## Steps
1. Pick the type: the first row that matches wins.
   | type | log it when | workflow | role |
   |---|---|---|---|
   | incident | a live or production service is broken or degraded right now | omi-flow-incident | engineer / devops |
   | security | a vulnerability, a secret leak, or a wrong permission/authz/data exposure | omi-flow-feature-sensitive | engineer |
   | bug | existing behaviour differs from the spec or an accepted criterion (test, review, PO or `FOUND:`) | omi-flow-bugfix | engineer |
   | change | the PO changes a requirement already accepted or running | omi-flow-change-request | Coordinator |
   | spike | a question must be answered first; the output is a recommendation, not product code | omi-flow-spike | researcher / architect |
   | chore | refactor, dependency upgrade, tech debt or CI/tooling, no behaviour change | omi-flow-refactor | engineer |
   | milestone | a release or date the PO commits to | none, never run | - |
   | epic | an outcome larger than one session, split into children | none, never run | - |
   | fr | one user-visible behaviour from the spec | omi-flow-feature / omi-flow-feature-ui | engineer |
   | nfr | a measurable quality target with a number | omi-flow-feature / omi-flow-feature-sensitive | engineer |
   | task | one-session work that fits none of the above | lightest fitting | engineer |
2. Pick the `parent` from the tree; anything else is reported by `tasks.tree_errors`.
   | type | parent may be | children may be |
   |---|---|---|
   | milestone | none (root) | epic, fr, nfr, task, chore, spike |
   | epic | milestone or none | fr, nfr, task, chore, spike |
   | fr, nfr | epic, milestone or none | task, spike, bug |
   | incident | none, milestone or epic | bug, security, chore (root-cause fixes) |
   | change | the fr / nfr / epic / milestone it changes | task (follow-up work) |
   | task, bug, security, spike, chore | any of the above, or none | none (leaf) |
   A bug or security issue that breaks a known fr / nfr takes it as `parent`. A hole found while doing task X records `Source task: TASK-X` in its Goal and does not take X as parent (X is a leaf). `refs:` is only for `.omi/references/` documents, never task ids.
3. Log it where it belongs:
   - A project issue: `.omi/tasks/TASK-NNN.md` from `_template.md` in that project's state (detached: `~/.omi/state/...`). Commit and push it the moment it is found, before any other step.
   - An issue about omi itself: `omi improve`, into omi's own state, never the project.
   - Decisions: `.omi/decisions.md`. An incident's timeline: `omi note` under the incident's `## Steps` / `## Reports`.
   - GitHub issues and PR comments are mirrors; the board reads only state.
4. Write the body under `## Goal`. All types: English imperative title of at most 72 characters; `type`, `parent`, `workflow`, `role`, minimum `scope`, testable `## Acceptance criteria`; never paste secrets or tokens. Then per type:
   - bug: Symptom, Expected, Steps to reproduce, Evidence (test, log line or command output), Source (task / agent / PO's words).
   - security: Impact, Boundary crossed, How verified, Evidence with secrets redacted.
   - incident: Started at, Impact (who / what), Current state; timeline lines via `omi note` as it develops.
   - change: What changes, the PO's words, affected tasks as `TASK-NNN`, what happens to running work.
   - spike: Question, Time-box (one session), Output (recommendation in `## Reports` plus follow-up tasks).
   - chore: Why now, and "no behaviour change" as a criterion.
   - milestone / epic: the outcome and the date or exit criterion. Status comes from the children; never run.

## Outputs and evidence
- A committed task file whose type, parent and workflow pass `omi status` and `omi step <ID> next` without a WARN.

## Stop and escalate
- No row fits, or the parent is unclear: ask the PO one pick-list question.

## Tools needed
- Read, Write, Edit.
