---
id: TASK-092
title: Bump omi to 0.3.1
status: in-progress
depends: TASK-089, TASK-090, TASK-091
plan: PLAN-002
scope: pyproject.toml, README.md, tests/test_omi.py, .omi/version, src/omi/template_shas.json, AGENTS.md, src/omi/template/AGENTS.md, .omi/skills/workflow/omi-skill-task-brief/SKILL.md, src/omi/template/dot-omi/skills/workflow/omi-skill-task-brief/SKILL.md, .omi/skills/CATALOG.md
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: haiku
effort: low
step_settings:
workflow: omi-flow-feature
step:
---
## Goal
Release prep for PLAN-002: version 0.3.1 everywhere `omi --version` and the rc tag read it, as in TASK-088.

## Acceptance criteria
- [ ] `omi --version` prints 0.3.1; `.omi/version` is 0.3.1; 0.3.1 template shas recorded (after the follow-up edits below, so they match).
- [ ] TASK-091 follow-ups: `tokens:` in both omi-skill-task-brief copies equals the real count (`omi skills` catalog value); AGENTS.md (both copies) quota line reads "The Coordinator sets `model`/`effort` (and `tool`) per task in the task file at task start ...".
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next: after merge: omi-release (rc), PO merges staging, then promote + tag v0.3.1; then `/omi-upgrade` in omi-board.
