---
id: TASK-037
title: Workflows - release and promote (migrate omi-release)
status: done
depends: TASK-032, TASK-031
scope: .omi/workflows/**, src/omi/template/dot-omi/workflows/**, .claude/skills/omi-release/**, src/omi/template/dot-claude/skills/omi-release/**, tests/**
role: omi-agent-engineer
skills: []  # step build adds omi-skill-lean-implementation
workflow: omi-flow-feature
step: accept
---
## Goal
The release flow exists as two workflows, and `omi-release` only starts them, with no change in behaviour.

### Brief
- Create `.omi/workflows/omi-flow-release.md` (old phase 1, candidate) and `.omi/workflows/omi-flow-promote.md` (old phases 2 promote and 3 tag); byte-identical copies in `src/omi/template/dot-omi/workflows/`. Layout as `.omi/workflows/omi-flow-feature.md`; at most 2000 tokens each.
- Every numbered step of the old `.claude/skills/omi-release/SKILL.md` (phase 1: 8 steps, phase 2: 4, phase 3: 4) maps to a workflow step or to its playbook text, with its exact commands, names (`rc-<YYYYMMDD>-<sha7>`, `v<YYYY.MM.DD>`, `.2`, `.3`), stop conditions and the "Create a merge commit" rule verbatim.
- Steps run as `coordinator` (they need `gh`/`git push` on the host). Use step skill `omi-skill-release-checklist` on the candidate and promote steps and `omi-skill-rollback` where the rollback plan is written. PO merges are `po` gate steps; nothing merges into `staging` or `main`.
- `omi-release/SKILL.md` (root and template, identical) keeps its frontmatter (`disable-model-invocation: true`, `argument-hint`) and phases `[promote|tag]`, but its body only says which workflow and step to run (`omi-flow-release`, or `omi-flow-promote` from the promote or tag step) plus the never-merge rule.
- Regenerate with `python -m omi workflows`; `python -m omi workflows --check`; tests `python3 tests/test_omi.py`.

## Acceptance criteria
- [x] `omi-flow-release` and `omi-flow-promote` workflows reproduce every step and PO gate of the current omi-release skill (merges into staging/main stay with the PO).
- [x] `omi-release` becomes a thin entry that starts the workflow; no step of the old flow is lost (checked against the old file in the review).
- [x] `python3 tests/test_omi.py` and `python -m omi workflows --check` pass; template copies identical (`diff -r` for workflows and the skill).
- [x] In the Checkpoint, a table maps each old step (phase.step) to its new location.

## Checkpoint
Done: omi-flow-release, omi-flow-promote (+template copies, CATALOG), thin omi-release skill (root+template).
Not done: nothing. Note: PO gates use role `coordinator` (role `po` is not a valid role).
Tests: tests/test_omi.py ok; omi workflows --check ok (11); diff -r identical.
Map old step -> new:
| old | new |
|---|---|
| 1.1-1.4 | omi-flow-release step candidate |
| 1.5-1.8 | omi-flow-release step pr |
| (PO merge staging) | omi-flow-release step merge-staging (po gate) |
| 2.1-2.4 | omi-flow-promote step promote |
| (PO merge main) | omi-flow-promote step merge-main (po gate) |
| 3.1-3.4 | omi-flow-promote step tag |
Next: TASK-038

## Steps
- plan started 2026-10-25 22:24
- plan done 2026-10-25 22:24
- build started 2026-10-25 22:24
- build done 2026-10-25 22:25
- review started 2026-10-25 22:25
- review done 2026-10-25 22:26
- accept started 2026-10-25 22:26
PO approval accept: Chấp nhận, merge (Recommended)
- accept done 2026-10-25 22:28

## Usage
| role | model | effort | input | output | cache | duration | skills read |
|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 16 | 5640 | 215528 | 68s | 1/1 omi-skill-lean-implementation |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 8 | 1845 | 116188 | 32s | - |
