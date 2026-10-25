---
id: TASK-046
title: Typed omi- names for every skill, agent and workflow, enforced by the validators
status: in-progress
depends: TASK-028
scope: .omi/skills/**, .omi/agents/**, src/omi/template/dot-omi/skills/**, src/omi/template/dot-omi/agents/**, src/omi/__init__.py, tests/test_omi.py, .claude/skills/**, src/omi/template/dot-claude/skills/**, AGENTS.md, src/omi/template/AGENTS.md, README.md, docs/**, .omi/decisions.md, .omi/tasks/_template.md, src/omi/template/dot-omi/tasks/_template.md
---
## Goal
Every skill, agent (role) and workflow name carries `omi-` plus its kind, so it is obvious in any list or log what it is and that it belongs to the OMI squad: skills `omi-skill-<name>`, agents `omi-agent-<name>`, workflows `omi-flow-<name>`. The four PO commands (`omi-idea`, `omi-task`, `omi-release`, `omi-status`) keep their names and are not renamed.

## Acceptance criteria
- [ ] Skills renamed (folder, frontmatter `id`, catalog, template copy, every reference): `write-skill`, `brainstorm-ac`, `task-brief`, `change-request`, `lean-implementation`, `verify-evidence`, `debug-root-cause`, `diff-security-review`, `ci-workflow-audit`, `simplify-review`, `release-checklist`, `rollback`, `incident`, `docker-worker-pitfalls`, `windows-powershell` -> `omi-skill-<same>`. Group folders (`workflow`, `quality`, ...) keep their names.
- [ ] Roles renamed: `engineer` -> `omi-agent-engineer`, `reviewer` -> `omi-agent-reviewer` (file names, `role:` default, `omi run`, `omi worker` defaults, container names, usage tables, AGENTS.md, omi-task skill, README, tests).
- [ ] `python -m omi skills --check` rejects a skill id that does not start with `omi-skill-`; `python -m omi agents` rejects a role name that does not start with `omi-agent-`; the workflow prefix `omi-flow-` is documented in `omi-skill-write-skill` and enforced when TASK-032 adds the workflow validator.
- [ ] Old names keep working nowhere: unknown-id errors name the expected prefix; no stale references remain (`grep` for the old ids in `.omi`, `src`, `docs`, `.claude`, `README.md` finds only history in task files and decisions).
- [ ] The PO commands keep their names. Existing task files with `role: engineer` or `skills: [old-id]` still resolve until closed: old values in done tasks are left as history.
- [ ] `python tests/test_omi.py` passes; template and root copies identical.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-026
