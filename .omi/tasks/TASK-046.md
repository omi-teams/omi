---
id: TASK-046
title: omi- prefix for every skill, role and workflow name, enforced by the validators
status: planned
depends: TASK-028
scope: .omi/skills/**, .omi/agents/**, src/omi/template/dot-omi/skills/**, src/omi/template/dot-omi/agents/**, src/omi/__init__.py, tests/test_omi.py, .claude/skills/**, src/omi/template/dot-claude/skills/**, AGENTS.md, src/omi/template/AGENTS.md, README.md, docs/**, .omi/decisions.md
---
## Goal
Every skill id, role name and (future) workflow name starts with `omi-`, so it is obvious in any list or log that it belongs to the OMI squad. Prefixes: skills `omi-<name>`, roles `omi-<name>`, workflows `omi-flow-<name>` (so a workflow never collides with a skill or with the PO commands `omi-release`, `omi-task`, `omi-idea`, `omi-status`).

## Acceptance criteria
- [ ] Skills renamed (folder, frontmatter `id`, catalog, template copy, every reference): `write-skill`, `brainstorm-ac`, `task-brief`, `change-request`, `lean-implementation`, `verify-evidence`, `debug-root-cause`, `diff-security-review`, `ci-workflow-audit`, `simplify-review`, `release-checklist`, `rollback`, `incident`, `docker-worker-pitfalls`, `windows-powershell` -> `omi-<same>`. Group folders (`workflow`, `quality`, ...) keep their names.
- [ ] Roles renamed: `engineer` -> `omi-engineer`, `reviewer` -> `omi-reviewer` (file names, `role:` default, `omi run`, `omi worker` defaults, container names, usage tables, AGENTS.md, omi-task skill, README, tests).
- [ ] `python -m omi skills --check` rejects a skill id without the `omi-` prefix; `python -m omi agents` rejects a role name without it; the same rule is documented in `omi-write-skill` for the workflow prefix `omi-flow-`.
- [ ] Old names keep working nowhere: unknown-id errors name the expected prefix; no stale references remain (`grep` for the old ids in `.omi`, `src`, `docs`, `.claude`, `README.md` finds only history in task files and decisions).
- [ ] The PO commands keep their names. Existing task files with `role: engineer` or `skills: [old-id]` still resolve until closed: old values in done tasks are left as history.
- [ ] `python tests/test_omi.py` passes; template and root copies identical.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-026
