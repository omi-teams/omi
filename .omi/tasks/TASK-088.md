---
id: TASK-088
title: Bump omi to 0.3.0
status: in-progress
depends: TASK-087
plan: PLAN-001
scope: pyproject.toml, README.md, tests/test_omi.py, .omi/version, src/omi/template_shas.json
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: haiku
effort: low
workflow: omi-flow-feature
step: build
---
## Goal
Release prep for 0.3.0 (PLAN-001 done criteria). Version is SemVer 0.x with `pyproject.toml` as the only source (decision 2026-10-26, TASK-074). Bump it so `omi --version` and the install instructions match the v0.3.0 tag the PO creates at promote.

## Acceptance criteria
- [ ] `pyproject.toml` version is `0.3.0`; `python -m omi --version` prints `omi 0.3.0`.
- [ ] README install line and `omi --version` example say `v0.3.0` / `omi 0.3.0`.
- [ ] This repo's `.omi/version` is `0.3.0`.
- [ ] `src/omi/template_shas.json` gains a `0.3.0` entry equal to the current template's hashes (`python -m omi template-shas src/omi/template 0.3.0`); the `0.2.0` entry is unchanged.
- [ ] Tests updated for the new version (only the version assertion; tag-parsing fixtures that use `v0.2.0` as sample data stay) and pass on the Linux worker and the Windows host.

## Checkpoint
Done: pyproject.toml, README (install tag + --version example), .omi/version, template_shas.json 0.3.0 entry (python -m omi template-shas src/omi/template 0.3.0), tests/test_omi.py version assertion (v0.2.0 tag fixtures kept).
Not done: Windows host test run (Linux only here).
Tests: python3 tests/test_omi.py -> exit 0; `python3 -m omi --version` -> omi 0.3.0.
Next: start with `omi-task TASK-088`. After merge: omi-release (rc), PO merges staging, then promote + tag v0.3.0.

Coordinator (Windows host): tests ok; template_shas['0.3.0'] == template_shas(); `PYTHONPATH=src python -m omi --version` -> omi 0.3.0.

## Steps
- plan started 2026-10-27 22:29
- plan done 2026-10-27 22:29
- build started 2026-10-27 22:29

## Reports
2026-10-27 22:37 omi-agent-engineer (claude):
> DONE
> 
> Files changed: `pyproject.toml`, `README.md`, `.omi/version`, `src/omi/template_shas.json` (added `0.3.0`, `0.2.0` untouched), `tests/test_omi.py` (version assertion only), `.omi/tasks/TASK-088.md` (checkpoint).
> Test: `python3 tests/test_omi.py` exits 0 with no failures; `python3 -m omi --version` prints `omi 0.3.0`.
> Open: Windows host test run not done (Linux only). Test runs take over 2 minutes, so run it in the background.
> Suggested commit: `chore(release): bump omi to 0.3.0`
2026-10-27 22:40 hook post-run passed:
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
> create .omi/skills/quality/omi-skill-verify-evidence/SKILL.md
> create .omi/skills/ui/omi-skill-ui-a11y-review/SKILL.md
> create .omi/skills/ui/omi-skill-ui-direction/SKILL.md
> create .omi/skills/ui/omi-skill-ui-direction/references/style-presets.md
> [... truncated ...]
> ok

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-haiku-5-5 | low | 24 | 3476 | 305724 | 497s | 1/1 omi-skill-lean-implementation | - |
