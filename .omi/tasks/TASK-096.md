---
id: TASK-096
title: Rename omi-squad2 to omi in code, skills and docs
status: in-progress
depends: TASK-093, TASK-094
plan: PLAN-003
scope: .claude/skills/omi-upgrade/SKILL.md, .omi/skills/delivery-ops/omi-skill-docker-worker-pitfalls/SKILL.md, .omi/skills/delivery-ops/omi-skill-incident/SKILL.md, .omi/skills/delivery-ops/omi-skill-release-checklist/SKILL.md, .omi/skills/delivery-ops/omi-skill-rollback/SKILL.md, .omi/skills/delivery-ops/omi-skill-windows-powershell/SKILL.md, README.md, src/omi/cli.py, src/omi/upgrade.py, src/omi/template/dot-claude/skills/omi-upgrade/SKILL.md, src/omi/template/dot-omi/skills/delivery-ops/omi-skill-docker-worker-pitfalls/SKILL.md, src/omi/template/dot-omi/skills/delivery-ops/omi-skill-incident/SKILL.md, src/omi/template/dot-omi/skills/delivery-ops/omi-skill-release-checklist/SKILL.md, src/omi/template/dot-omi/skills/delivery-ops/omi-skill-rollback/SKILL.md, src/omi/template/dot-omi/skills/delivery-ops/omi-skill-windows-powershell/SKILL.md, tests/test_omi.py, src/omi/template_shas.json, .omi/skills/CATALOG.md
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
The PO renamed the GitHub repo `omi-teams/omi-squad2` to `omi-teams/omi` (2026-10-28). Every default URL, install command and skill text points to the new name, so 0.3.2 installs from `omi-teams/omi`.

## Acceptance criteria
- [ ] `git grep omi-squad2` finds nothing outside `.omi/tasks`, `.omi/decisions.md`, `.omi/plans` and `docs/` (history stays as written).
- [ ] `OMI_REPO` default is `https://github.com/omi-teams/omi`; README install commands use it; local worktree paths in skill text use a placeholder (`<repo-name>`), not a hard-coded folder.
- [ ] Repo copies equal their template copies; catalogs regenerated; template shas updated if the tests require it. All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:
