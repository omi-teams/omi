---
id: TASK-102
title: Bump omi to 0.4.0
status: in-progress
depends: TASK-101
plan: PLAN-004
scope: pyproject.toml, README.md, tests/test_omi.py, .omi/version, src/omi/template_shas.json
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: haiku
effort: low
step_settings:
workflow: omi-flow-feature
step: build
---
## Goal
Release prep for PLAN-004, as in TASK-095.

## Acceptance criteria
- [ ] `omi --version` prints 0.4.0; `.omi/version` is 0.4.0; 0.4.0 template shas recorded; README documents detached mode in at most 15 lines.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done: version 0.4.0 in pyproject.toml, .omi/version, README (install tag + --version line), tests/test_omi.py version assertion; template_shas.json 0.4.0 entry recorded (62 files, equals omi.upgrade.template_shas()); 0.3.2 entry untouched. README detached-mode paragraph already documents the feature in under 15 lines; left as is.
Not done: Windows host test run (not possible in container).
Tests: `python3 tests/test_omi.py` exit 0 (Linux container); `PYTHONPATH=src python3 -m omi --version` -> omi 0.4.0.
Next: Coordinator runs the Windows host test and merges.

## Steps
- plan started 2026-10-29 13:39
- plan done 2026-10-29 13:39
- build started 2026-10-29 13:39

## Reports
2026-10-29 13:45 omi-agent-engineer (claude):
> DONE
> 
> Files changed: pyproject.toml, README.md, tests/test_omi.py, .omi/version, src/omi/template_shas.json, .omi/tasks/TASK-102.md (checkpoint).
> Test: `python3 tests/test_omi.py` exit 0 on the Linux container. `PYTHONPATH=src python3 -m omi --version` prints `omi 0.4.0`. The 0.4.0 shas entry (62 files) equals `omi.upgrade.template_shas()`.
> Not run: the Windows host test run, which the second criterion needs. The README detached-mode paragraph already fits in under 15 lines, so I left it as is.
> Commit: `chore(release): bump omi to 0.4.0`
> Open issues: the Windows host test is still pending.
2026-10-29 13:48 hook post-run passed:
> OMI: outside.py is outside the scope of TASK-097. Stop and report NEEDS SCOPE to the Coordinator.
> OMI: projects/sample/.omi/tasks/TASK-097.md is outside the task worktree.
> OMI: .omi/tasks/TASK-097.md is outside the scope of TASK-097. Stop and report NEEDS SCOPE to the Coordinator.
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
> [... truncated ...]
> ok

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-haiku-5-5 | low | 24 | 3748 | 356208 | 335s | 1/1 omi-skill-lean-implementation | - |
