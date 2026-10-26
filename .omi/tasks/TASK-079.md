---
id: TASK-079
title: omi upgrade and /omi-upgrade - install a newer omi and update unmodified template files
status: in-progress
depends: TASK-078
scope: src/omi/__init__.py, src/omi/template_shas.json, pyproject.toml, tests/**, src/omi/template/**, .claude/skills/omi-upgrade/**, AGENTS.md, README.md
role: omi-agent-engineer
skills: [omi-skill-windows-powershell]
refs:
plan: PLAN-001
tool: claude
model: sonnet
effort: medium
workflow: omi-flow-feature-sensitive
step: build
---
## Goal
A project that runs omi moves to a newer omi with one PO command: install the new version, add new template files, update template files the project never changed, and list the ones it did change for the PO to decide. This also fixes Dockerfile drift.

## Acceptance criteria
- [ ] `omi init` writes `.omi/manifest.json`: `{"version": X, "files": {"<project path>": "<sha256 of the template file it installed>"}}` for every template file it creates. A project without a manifest gets one on its next `omi init`/`omi upgrade`, recording only files that are byte-identical (CRLF/LF ignored) to the current template or to a released template listed in `src/omi/template_shas.json` (`{"0.2.0": {path: sha}}`, built once from tag v0.2.0, shipped as package data). Tested.
- [ ] `omi upgrade --check` lists remote tags (`git ls-remote --tags` of `omi_repo` in `.omi/config.json`, default https://github.com/omi-teams/omi-squad2), picks the highest `vX.Y.Z` (SemVer, ignores date tags), and prints `omi <installed> -> <latest>` or `up to date`. Tested with a fake subprocess.
- [ ] `omi upgrade [--to vX.Y.Z]` runs `python -m pip install --user --upgrade "git+<omi_repo>@<tag>"`, then runs `python -m omi upgrade --apply` in a new process so the newly installed omi updates the project. Tested on argv.
- [ ] `omi upgrade --apply`: per template file, missing in the project -> create; unchanged since install (sha matches manifest) -> overwrite with the new template; changed by the project -> keep it, print `kept (modified): <path>`, and write the new version next to it as `<path>.omi-new`. Then update `.omi/manifest.json` and `.omi/version`, regenerate catalogs, print a summary. Never touch `.omi/tasks`, `.omi/plans/PLAN-*` other than PLAN-000, `.omi/decisions.md`; `.omi/config.json` only gains new keys from the template, existing values stay. Tested.
- [ ] Skill `.claude/skills/omi-upgrade/SKILL.md` (root and template) and an AGENTS.md line for `omi-upgrade`: run `--check`, ask the PO (pick-list) which version, run the upgrade, show the summary, for each `.omi-new` ask the PO keep / take new / merge, then commit on `development` and run the tests.
- [ ] README upgrade section uses `/omi-upgrade` or `python -m omi upgrade`.
- [ ] Real check (Coordinator): a sandbox initialised with 0.2.0 files plus one locally edited template file runs `--apply` with this branch's code: new files created, unchanged files updated, the edited file kept with a `.omi-new` next to it.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done: manifest in init, upgrade --check/--to/--apply, template-shas CLI, empty template_shas.json, skill (root+template), AGENTS.md lines, README, tests.
Not done: v0.2.0 hashes (Coordinator: `python -m omi template-shas <v0.2.0 export>/src/omi/template 0.2.0`); real sandbox check; Windows run.
Tests: python3 tests/test_omi.py ok (Linux)
Next: Coordinator review

Coordinator note for build: git does not work in the worker, so the v0.2.0 hashes cannot be read there. Provide a function that maps a template directory to {posix rel: norm_sha} and a CLI entry the Coordinator can run on the host, e.g. `python -m omi template-shas <template-dir> <version>` writing/merging `src/omi/template_shas.json`. Commit an empty `{}` placeholder; the Coordinator runs it against an export of tag v0.2.0 and commits the data. Tests use a tmp template dir.

Coordinator host steps (2026-10-26):
- template_shas.json: `git archive v0.2.0 src/omi/template` exported, `python -m omi template-shas <export>/src/omi/template 0.2.0` with this branch -> 61 files.
- Windows: `python tests/test_omi.py` -> rc=0, ok.
- Real check: sandbox `git init` + v0.2.0 `omi init` (no manifest), appended a line to .omi/agents/omi-agent-reviewer.md, then this branch's `omi upgrade --apply` -> `1 created, 8 updated, 1 kept`; created .claude/skills/omi-upgrade/SKILL.md, updated AGENTS.md, docker/Dockerfile, docker/proxy.py and 5 more; `kept (modified): .omi/agents/omi-agent-reviewer.md` with `omi-agent-reviewer.md.omi-new` next to it; .omi/version and .omi/manifest.json written.

## Steps
- plan started 2026-10-26 22:07
- plan done 2026-10-26 22:07
- architect started 2026-10-26 22:07
- architect done 2026-10-26 22:10
- build started 2026-10-26 22:10

## Reports
2026-10-26 22:08 omi-agent-architect (claude):
> RECOMMEND: B - a manifest plus a shipped `known_shas` file for v0.2.0, so a 0.2.0 project with no manifest (every project today) gets its unchanged files updated instead of flooded with `.omi-new`.
> OPTIONS: A: manifest only, backfilled from the current template / smallest and matches AC1 word for word, but on the first upgrade from 0.2.0 every unchanged file differs from the 0.3.0 template, so all are "kept (modified)" and the Coordinator real check fails; B: A plus `src/omi/template_shas.json` (`{"0.2.0": {path: sha}}`, built once from tag v0.2.0) so a file matching a released sha is backfilled as unmodified / one extra data file, its hashes must be correct, and it extends AC1's backfill rule; C: hashes computed at run time from `git show v0.2.0` / git is often missing in the installed package and needs the omi repo, so it is fragile.
> [... truncated ...]
> NEEDS DECISION: AC1 says backfill records only files identical to the *current* template, but the real check expects a no-manifest 0.2.0 sandbox to have its unchanged files *updated*. Approve B's extension (also match released v0.2.0 hashes), or keep A and have the real check run on a sandbox made by this branch's `omi init`?
2026-10-26 22:13 omi-agent-engineer (claude):
> DONE (the v0.2.0 hashes still need to be generated on the host, see open issues)
> - Files changed:
>   - `src/omi/__init__.py`, `src/omi/template_shas.json` (`{}` placeholder), `pyproject.toml` (package data)
>   - `tests/test_omi.py`
>   - `.claude/skills/omi-upgrade/SKILL.md` and the same file under `src/omi/template/dot-claude/skills/`
>   - `AGENTS.md` and `src/omi/template/AGENTS.md`, `README.md`, and the TASK-079 checkpoint
> - Commit message: `feat: omi upgrade with install manifest, .omi-new for modified template files`
> - Tests: `python3 tests/test_omi.py` passes on Linux. I did not run the Windows host or the real sandbox check.
> - Open issue: `template_shas.json` is empty. Run `python -m omi template-shas <v0.2.0 export>/src/omi/template 0.2.0` on the host and commit the result. Until then, a 0.2.0 project without a manifest will see its edited and unedited files all kept as modified.
> - `CATALOG.md` files are excluded from the manifest and from `--apply`, because every `init` and `--apply` regenerates them.
> - `.omi/tasks/_template.md` is updated by `--apply`; every other file under `.omi/tasks` is untouched.
> - `--check` prints the latest tag without the `v` (`omi 0.2.0 -> 0.3.0`). The pip and `--apply` subprocess calls use `sys.executable`, not a literal `python`.
2026-10-26 22:14 hook post-run passed:
> Conflict. The container name "/tmp31dl45um-TASK-001-engineer-codex-gpt-x-medium-151325" is already in useBind for 0.0.0.0:8080 failed: port is already in usewrote /tmp/tmp9xre0yaz/.omi/skills/CATALOG.md (2 skills)
> create AGENTS.md
> create docker/Dockerfile
> create docker/prove.sh
> create docker/proxy.py
> create .claude/settings.json
> create .claude/skills/omi-idea/SKILL.md
> create .claude/skills/omi-release/SKILL.md
> create .claude/skills/omi-status/SKILL.md
> create .claude/skills/omi-task/SKILL.md
> create .claude/skills/omi-upgrade/SKILL.md
> create .omi/agents/omi-agent-architect.md
> create .omi/agents/omi-agent-designer-ui.md
> create .omi/agents/omi-agent-devops.md
> create .omi/agents/omi-agent-docs-writer.md
> create .omi/agents/omi-agent-engineer.md
> create .omi/agents/omi-agent-qa-tester.md
> create .omi/agents/omi-agent-researcher.md
> create .omi/agents/omi-agent-reviewer.md
> create .omi/agents/omi-agent-security-reviewer.md
> create .omi/config.json
> create .omi/decisions.md
> create .omi/hooks/post-run.sh
> create .omi/plans/PLAN-000.md
> create .omi/references/nextjs-app-router.md
> create .omi/references/postgres-conventions.md
> create .omi/rules/docker.md
> create .omi/rules/go.md
> create .omi/rules/nextjs.md
> create .omi/rules/postgres.md
> create .omi/rules/python.md
> create .omi/skills/.gitkeep
> create .omi/skills/data/omi-skill-data-review/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-docker-worker-pitfalls/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-incident/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-release-checklist/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-rollback/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-windows-powershell/SKILL.md
> create .omi/skills/qa-web/omi-skill-web-qa/SKILL.md
> create .omi/skills/quality/omi-skill-ci-workflow-audit/SKILL.md
> create .omi/skills/quality/omi-skill-debug-root-cause/SKILL.md
> create .omi/skills/quality/omi-skill-diff-security-review/SKILL.md
> create .omi/skills/quality/omi-skill-simplify-review/SKILL.md
> [... truncated ...]
> ok

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 12 | 4515 | 152074 | 53s | - | n/a |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 18 | 11516 | 297805 | 180s | 2/2 omi-skill-windows-powershell omi-skill-lean-implementation | - |
