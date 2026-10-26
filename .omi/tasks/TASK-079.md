---
id: TASK-079
title: omi upgrade and /omi-upgrade - install a newer omi and update unmodified template files
status: planned
depends: TASK-078
scope: src/omi/__init__.py, tests/**, src/omi/template/**, .claude/skills/omi-upgrade/**, AGENTS.md, README.md
role: omi-agent-engineer
skills: [omi-skill-windows-powershell]
refs:
plan: PLAN-001
tool:
model: sonnet
effort: medium
workflow: omi-flow-feature-sensitive
step:
---
## Goal
A project that runs omi moves to a newer omi with one PO command: install the new version, add new template files, update template files the project never changed, and list the ones it did change for the PO to decide. This also fixes Dockerfile drift.

## Acceptance criteria
- [ ] `omi init` writes `.omi/manifest.json`: `{"version": X, "files": {"<project path>": "<sha256 of the template file it installed>"}}` for every template file it creates. A project without a manifest gets one on its next `omi init`/`omi upgrade`, recording only files that are byte-identical (CRLF/LF ignored) to the current template. Tested.
- [ ] `omi upgrade --check` lists remote tags (`git ls-remote --tags` of `omi_repo` in `.omi/config.json`, default https://github.com/omi-teams/omi-squad2), picks the highest `vX.Y.Z` (SemVer, ignores date tags), and prints `omi <installed> -> <latest>` or `up to date`. Tested with a fake subprocess.
- [ ] `omi upgrade [--to vX.Y.Z]` runs `python -m pip install --user --upgrade "git+<omi_repo>@<tag>"`, then runs `python -m omi upgrade --apply` in a new process so the newly installed omi updates the project. Tested on argv.
- [ ] `omi upgrade --apply`: per template file, missing in the project -> create; unchanged since install (sha matches manifest) -> overwrite with the new template; changed by the project -> keep it, print `kept (modified): <path>`, and write the new version next to it as `<path>.omi-new`. Then update `.omi/manifest.json` and `.omi/version`, regenerate catalogs, print a summary. Never touch `.omi/tasks`, `.omi/plans/PLAN-*` other than PLAN-000, `.omi/decisions.md`; `.omi/config.json` only gains new keys from the template, existing values stay. Tested.
- [ ] Skill `.claude/skills/omi-upgrade/SKILL.md` (root and template) and an AGENTS.md line for `omi-upgrade`: run `--check`, ask the PO (pick-list) which version, run the upgrade, show the summary, for each `.omi-new` ask the PO keep / take new / merge, then commit on `development` and run the tests.
- [ ] README upgrade section uses `/omi-upgrade` or `python -m omi upgrade`.
- [ ] Real check (Coordinator): a sandbox initialised with 0.2.0 files plus one locally edited template file runs `--apply` with this branch's code: new files created, unchanged files updated, the edited file kept with a `.omi-new` next to it.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:
