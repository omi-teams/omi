---
id: TASK-037
title: Workflows - release and promote (migrate omi-release)
status: in-progress
depends: TASK-032, TASK-031
scope: .omi/workflows/**, src/omi/template/dot-omi/workflows/**, .claude/skills/omi-release/**, src/omi/template/dot-claude/skills/omi-release/**, tests/**
role: omi-agent-engineer
skills: []  # step build adds omi-skill-lean-implementation
workflow: omi-flow-feature
step:
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
- [ ] `omi-flow-release` and `omi-flow-promote` workflows reproduce every step and PO gate of the current omi-release skill (merges into staging/main stay with the PO).
- [ ] `omi-release` becomes a thin entry that starts the workflow; no step of the old flow is lost (checked against the old file in the review).
- [ ] `python3 tests/test_omi.py` and `python -m omi workflows --check` pass; template copies identical (`diff -r` for workflows and the skill).
- [ ] In the Checkpoint, a table maps each old step (phase.step) to its new location.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-038
