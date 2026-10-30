---
id: TASK-102
title: Bump omi to 0.4.0
status: done
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
step: accept
---
## Goal
Release prep for PLAN-004, as in TASK-095.

## Acceptance criteria
- [x] `omi --version` prints 0.4.0; `.omi/version` is 0.4.0; 0.4.0 template shas recorded; README documents detached mode in at most 15 lines.
- [x] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Host: python tests/test_omi.py (Windows host, worktree) -> ok, exit 0; omi.core.version() -> 0.4.0
Done: version 0.4.0 in pyproject.toml, .omi/version, README (install tag + --version line), tests/test_omi.py version assertion; template_shas.json 0.4.0 entry recorded (62 files, equals omi.upgrade.template_shas()); 0.3.2 entry untouched. README detached-mode paragraph already documents the feature in under 15 lines; left as is.
Not done: Windows host test run (not possible in container).
Tests: `python3 tests/test_omi.py` exit 0 (Linux container); `PYTHONPATH=src python3 -m omi --version` -> omi 0.4.0.
Next: Coordinator runs the Windows host test and merges.

## Steps
PO approval accept: Chấp nhận, merge
- plan started 2026-10-29 13:39
- plan done 2026-10-29 13:39
- build started 2026-10-29 13:39
- build done 2026-10-29 13:48
- review started 2026-10-29 13:48
- review done 2026-10-29 13:54
- accept started 2026-10-29 13:54
- accept done 2026-10-29 13:55

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
2026-10-29 13:53 omi-agent-reviewer (claude):
> ```
> VERDICT: PASS
> - .omi/tasks/TASK-102.md:47 The worker's "hook post-run passed" report contains test-fixture output (TASK-097 "outside scope" messages and a long "create ..." list) that doesn't belong to this task -> trim it from the report. Not blocking; the task file is outside `scope` but it is only the checkpoint.
> AC: `omi --version` prints 0.4.0 ✓ pyproject.toml version = 0.4.0, and the test asserts `omi.core.version()` equals it. I did not run `omi --version`.
> AC: `.omi/version` is 0.4.0 ✓ the diff changes it from 0.3.2 to 0.4.0.
> AC: 0.4.0 template shas recorded ✓ in src/omi/template_shas.json, the "0.4.0" entry equals `omi.upgrade.template_shas()` (62 files). The 0.3.2 entry is unchanged. The two entries differ in one file, `.omi/hooks/post-run.sh`.
> AC: README documents detached mode in at most 15 lines ✓ the detached-mode paragraphs sit at about README.md lines 22-28, which is under 15 lines. The install tag and the `--version` comment now say 0.4.0.
> AC: All tests pass on the Linux worker ✓ `python3 tests/test_omi.py` exited 0.
> AC: All tests pass on the Windows host HOST needs the Windows host; the coordinator still has to run it.
> ```

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-haiku-5-5 | low | 24 | 3748 | 356208 | 335s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 10 | 1675 | 130504 | 241s | - | PASS c962098 |
