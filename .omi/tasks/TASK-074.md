---
id: TASK-074
title: Versioned omi package - omi --version, project version stamp, install from a tag
status: in-progress
depends:
scope: pyproject.toml, src/omi/__init__.py, tests/**, src/omi/template/**, README.md
role: omi-agent-engineer
skills: [omi-skill-windows-powershell]
refs:
plan:
tool:
model: sonnet
effort: medium
workflow: omi-flow-feature
step: build
---
## Goal
omi has one version (SemVer 0.x, in `pyproject.toml`), shows it, stamps it into each project on `omi init`, tells the PO when a project is older than the installed omi, and installs cleanly from a git tag. Bump to 0.2.0 (rules, references, plans, hooks, model per task).

## Acceptance criteria
- [ ] `pyproject.toml` is the only place the version is written; `version = "0.2.0"`.
- [ ] `omi --version` (and `omi version`) prints `omi 0.2.0`, read with `importlib.metadata`; when omi runs from a source checkout without being installed, it falls back to `pyproject.toml`. Tested both ways.
- [ ] `omi init` writes `.omi/version` with the running version (also when re-run on an existing project, so the stamp follows the files it added). Tested.
- [ ] `omi status` prints `omi <installed> (project <stamp>)` and, when the stamp is missing or older (SemVer compare, no new dependency), one line `run \`omi init\` to add the files of omi <installed>`. Tested.
- [ ] Every file under `src/omi/template` is covered by `[tool.setuptools.package-data]`, including dot-dirs stored as `dot-*`, `.sh` hooks and `references/` under skills. Tested by matching the globs against the file list.
- [ ] Template `post-run.sh` runs the `test` command from `.omi/config.json` when it is set, before the go/npm/pytest detection. Tested with `sh` in a temp dir.
- [ ] README install section: `pipx install git+https://github.com/omi-teams/omi-squad2@v0.2.0`, upgrade (`pipx install --force ...@<tag>`, then `omi init` in each project), `omi --version`.
- [ ] Real install (Coordinator, Windows host): `pip install` of this branch into a fresh venv, then `omi --version` and `omi init` into an empty dir create `.omi/version`, rules, references, plans and hooks.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Coordinator check round 1 FAIL (before review):
- `omi init` copies `src/omi/template/docker/__pycache__/proxy.cpython-313.pyc` (untracked, made when tests import docker/proxy.py; seen in the post-run output: "create docker/__pycache__/proxy.cpython-313.pyc"). `init` must skip `__pycache__` dirs and `*.pyc`, and the package must not ship them: add `[tool.setuptools.exclude-package-data] omi = ["**/__pycache__/*", "*.pyc"]` (or equivalent) and extend the package-data test so a `.pyc` under template is not covered. Test that init into an empty dir creates no `__pycache__`.
Done: version 0.2.0, omi --version/version, .omi/version stamp in init, status line + upgrade hint, package-data globs, post-run.sh config test, README, tests.
Not done: real install on Windows host (Coordinator).
Tests: python3 tests/test_omi.py ok (Linux).
Next: Coordinator reviews and runs Windows install check.

## Steps
- plan started 2026-10-26 14:55
- plan done 2026-10-26 14:55
- build started 2026-10-26 14:55

## Reports
2026-10-26 14:57 omi-agent-engineer (claude):
> DONE
> - Files changed: `pyproject.toml`, `src/omi/__init__.py`, `src/omi/template/dot-omi/hooks/post-run.sh`, `tests/test_omi.py`, `README.md`, `.omi/tasks/TASK-074.md` (checkpoint).
> - Version is 0.2.0, written only in `pyproject.toml`. `omi --version` and `omi version` print `omi 0.2.0`, read from the `omi-squad` package metadata, with a fallback to `pyproject.toml` in a source checkout.
> - `omi init` writes `.omi/version` on every run. `omi status` prints `omi X (project Y)`, plus the `run \`omi init\`...` line when the stamp is missing or older (SemVer compare, no new dependency).
> - `package-data` now has the globs `template/*`, `template/**/*` and `template/**/.*`; the last one is for `.gitkeep`. The test matches them against the template file list, including the `.sh` hooks and the skill `references/` dirs.
> - `post-run.sh` runs the `test` command from `.omi/config.json` before the go/npm/pytest detection. The test runs it with `sh` in a temp dir that also has a `go.mod`, and checks the exit code is the configured one.
> - README install section is added in Vietnamese, matching the rest of the file: install from the `v0.2.0` tag, upgrade, `omi --version`.
> - Tests: `python3 tests/test_omi.py` passes on Linux. The new test is `test_version_stamp_package_hook`.
> - Open: I did not run the real `pip install` into a fresh venv or the Windows host run (Coordinator).
> 
> Suggested commit: `feat: version omi 0.2.0 with --version, project version stamp and tag install`
2026-10-26 14:57 hook post-run passed:
> Conflict. The container name "/tmpvtef99pv-TASK-001-engineer-codex-gpt-x-medium-075709" is already in useBind for 0.0.0.0:8080 failed: port is already in usewrote /tmp/tmp5p8dss5h/.omi/skills/CATALOG.md (2 skills)
> create AGENTS.md
> create docker/Dockerfile
> create docker/__pycache__/proxy.cpython-313.pyc
> create docker/prove.sh
> create docker/proxy.py
> create .claude/settings.json
> create .claude/skills/omi-idea/SKILL.md
> create .claude/skills/omi-release/SKILL.md
> create .claude/skills/omi-status/SKILL.md
> create .claude/skills/omi-task/SKILL.md
> create .omi/agents/CATALOG.md
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
> create .omi/plans/CATALOG.md
> create .omi/plans/PLAN-000.md
> create .omi/references/CATALOG.md
> create .omi/references/nextjs-app-router.md
> create .omi/references/postgres-conventions.md
> create .omi/rules/CATALOG.md
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
> [... truncated ...]
> ok

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 18 | 5729 | 236552 | 87s | 2/2 omi-skill-windows-powershell omi-skill-lean-implementation | - |
