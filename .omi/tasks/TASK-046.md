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
Done: 15 skill folders and ids renamed to omi-skill-<name> (root and template); engineer/reviewer renamed to omi-agent-* (files, role:, defaults, usage rows, container labels); validators reject bad prefixes (skills --check, agents); write-skill documents omi-flow-; catalogs regenerated; tests updated and passing.
Not done: old role/skill values in open task files (`role: engineer`) do not resolve; no alias kept (criterion 16 conflicts with criterion 15, PO to decide). project-overview.md still has old names in prose (outside scope). Workflow prefix validator is TASK-032.
Tests: python tests/test_omi.py passes (exit 0).
Next: TASK-026

## Usage
| role | model | effort | input | output | cache | duration |
|---|---|---|---|---|---|---|
| engineer | claude-haiku-5-5 | low | 44 | 19632 | 1131971 | 132s |
| reviewer | claude-sonnet-5-5 | medium | 12 | 3252 | 302099 | 34s |
| engineer | claude-haiku-5-5 | low | 16 | 3996 | 192443 | 34s |

## Fix round 1 (only this)
1. `docs/verification.md` lines 8 and 27: revert to the original text (`git diff development -- docs/verification.md`); they record past runs and must stay as history.
2. `README.md` lines ~22, 24, 34, 41: prose that still names the roles `engineer` / `reviewer` -> `omi-agent-engineer` / `omi-agent-reviewer` (role names only, not the plain English word elsewhere).
3. Checkpoint in this file: remove the stale note saying the task templates are outside scope; they are now changed and in scope.
4. `src/omi/__init__.py` around line 610: error text "the engineer agent" -> "the omi-agent-engineer agent".
Run the whole `python3 tests/test_omi.py` and report its last line.
