---
id: TASK-094
title: Host-only criteria are confirmed by the Coordinator, not marked by the reviewer
status: planned
depends:
plan: PLAN-003
scope: .omi/agents/omi-agent-reviewer.md, src/omi/template/dot-omi/agents/omi-agent-reviewer.md, .claude/skills/omi-task/SKILL.md, src/omi/template/dot-claude/skills/omi-task/SKILL.md, .omi/agents/CATALOG.md, src/omi/template_shas.json, tests/test_omi.py
role: omi-agent-engineer
skills: []
refs: []
tool:
model:
effort:
step_settings:
workflow: omi-flow-feature-sensitive
step:
---
## Goal
On TASK-092 the reviewer gave PASS although "tests pass on the Windows host" could not run in its container, against its own UNVERIFIED rule. Host-only checks get one owner: the Coordinator, with evidence in the checkpoint.

## Acceptance criteria
- [ ] Reviewer prompt (both copies): a criterion that can only run on the host (e.g. "on the Windows host") is reported `HOST <criterion>` and does not block PASS; every other skipped or unexecuted criterion stays `UNVERIFIED` and blocks PASS.
- [ ] omi-task skill (both copies): before merge, the Coordinator runs the host checks and writes `Host: <command> -> <result>` in the task checkpoint; no merge without that line when the reviewer reported a `HOST` item.
- [ ] Repo copies equal their template copies; agents catalog regenerated; `omi skills --check` passes; template shas updated if the tests require it. All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:
