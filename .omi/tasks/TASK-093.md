---
id: TASK-093
title: /omi-upgrade applies project files when they are behind the installed omi
status: planned
depends:
plan: PLAN-003
scope: .claude/skills/omi-upgrade/SKILL.md, src/omi/template/dot-claude/skills/omi-upgrade/SKILL.md, src/omi/__init__.py, tests/test_omi.py, src/omi/template_shas.json
role: omi-agent-engineer
skills: []
refs: []
tool:
model:
effort:
step_settings:
workflow: omi-flow-feature
step:
---
## Goal
omi-board had omi 0.3.1 installed but 0.3.0 project files, and `/omi-upgrade` stopped at `up to date`. After this, an upgrade always ends with `.omi/version` equal to the installed version.

## Acceptance criteria
- [ ] `/omi-upgrade` step 1 (both copies): when `upgrade --check` says `up to date` but `.omi/version` is older than the installed omi (or missing), run `python -m omi upgrade --apply` and continue with steps 4-5 instead of stopping; stop only when both are current.
- [ ] `omi status` hint for an older project stamp names the same command the skill runs (`python -m omi upgrade --apply`, or `omi init` if that is what actually stamps; pick the one that does, and the test proves it updates `.omi/version`). Tested.
- [ ] Repo copy equals its template copy; template shas updated if the tests require it. All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:
