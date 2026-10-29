---
id: TASK-111
title: Bump omi to 0.4.1
status: in-progress
depends: TASK-110, TASK-112
plan: PLAN-005
scope: pyproject.toml, README.md, tests/test_upgrade.py, tests/test_cli.py, .omi/version, src/omi/template_shas.json, src/omi/app/cli.py, .omi/tasks/TASK-111.md, src/omi/project/tasks.py
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: haiku
effort: low
step_settings:
workflow: omi-flow-feature
step: build
---
## Goal
Release prep for PLAN-005, as in TASK-102.

## Acceptance criteria
- [ ] `omi --version` prints 0.4.1; `.omi/version` is 0.4.1; 0.4.1 template shas recorded.
- [ ] The CLI usage line for `step` lists `next|done|back|skip|approve|reopen` (wherever cli.py lives after TASK-112).
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done: Bumped package/project version to 0.4.1, recorded current template hashes, updated README, expanded CLI step usage and its test expectation, and corrected the invalid-action usage message in `src/omi/project/tasks.py`.
Not done: Windows host test run.
Tests: `python3 tests/test_omi.py` completed with `ok` on Linux (exit 0).
Next: Coordinator runs `python3 tests/test_omi.py` on the Windows host.

## Steps
- plan started 2026-10-29 21:21
- plan done 2026-10-29 21:21
- build started 2026-10-29 21:21

## Reports
2026-10-29 21:22 omi-agent-engineer (codex):
> DONE
> Files changed: `pyproject.toml`, `.omi/version`, `README.md`, `src/omi/app/cli.py`, `src/omi/template_shas.json`, `tests/test_upgrade.py`, `tests/test_cli.py`, `.omi/tasks/TASK-111.md`
> Suggested commit: `chore: bump omi to 0.4.1`
> Test: `python3 tests/test_omi.py` completed with `ok` on Linux.
> Open issue: Windows host test run remains for the coordinator.
2026-10-29 21:26 hook post-run FAILED (exit 1):
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
> [... truncated ...]
> AssertionError: (['bogus'], 1, '', 'usage: omi step <TASK-ID> next|done|back|skip --why <reason>\n')
2026-10-29 21:30 omi-agent-engineer (codex):
> DONE
> Files changed: `src/omi/project/tasks.py`, `.omi/tasks/TASK-111.md`
> Suggested commit: `fix: update step usage message`
> Test: `python3 tests/test_omi.py` completed with `ok` on Linux (exit 0).
> Open issue: Windows host test run remains for the coordinator.
2026-10-29 21:34 hook post-run passed:
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
| omi-agent-engineer | gpt-6-luna (codex) | low | 388130 | 1838 | 355328 | 70s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-engineer | gpt-6-luna (codex) | low | 358585 | 1704 | 302976 | 240s | 1/1 omi-skill-lean-implementation | - |
