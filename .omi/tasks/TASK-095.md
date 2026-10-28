---
id: TASK-095
title: Bump omi to 0.3.2
status: done
depends: TASK-093, TASK-094, TASK-096
plan: PLAN-003
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
Release prep for PLAN-003: version 0.3.2 everywhere `omi --version` and the rc tag read it, as in TASK-092.

## Acceptance criteria
- [x] `omi --version` prints 0.3.2; `.omi/version` is 0.3.2; 0.3.2 template shas recorded.
- [x] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done: version 0.3.2 in pyproject.toml, .omi/version, README (install tag + --version), tests/test_omi.py version assertion; template_shas.json 0.3.2 entry recorded after all edits (62 files, equals omi.template_shas()); 0.3.1 entry untouched.
Not done: -
Tests: `python3 tests/test_omi.py` exit 0 (Linux worker); `PYTHONPATH=src python3 -m omi --version` -> omi 0.3.2.
Host: python tests/test_omi.py (Windows) -> exit 0, ok; 0.3.2 shas recomputed on host = recorded (62/62)
Next: merge

## Steps
- plan started 2026-10-28 16:52
- plan done 2026-10-28 16:52
- build started 2026-10-28 16:52
- build done 2026-10-28 17:00
- review started 2026-10-28 17:00
- review done 2026-10-28 17:05
- accept started 2026-10-28 17:05

## Reports
2026-10-28 16:57 omi-agent-engineer (claude):
> DONE
> 
> Files changed: pyproject.toml, .omi/version, README.md (install tag and `--version` line), tests/test_omi.py (version assertion), src/omi/template_shas.json (new 0.3.2 entry, 62 files, recorded after all edits), .omi/tasks/TASK-095.md (checkpoint).
> Test: `python3 tests/test_omi.py` exited 0 on the Linux container. `PYTHONPATH=src python3 -m omi --version` prints `omi 0.3.2`. Not run: the Windows host.
> Commit: `chore(release): bump omi to 0.3.2`
> Open issues: the Windows host test run is still pending, as the acceptance criteria require. I did not run `pip install .` (the container has no pip).
2026-10-28 16:59 hook post-run passed:
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
2026-10-28 17:05 omi-agent-reviewer (claude):
> ```
> VERDICT: PASS
> AC: `omi --version` prints 0.3.2; `.omi/version` is 0.3.2; 0.3.2 template shas recorded. ✓ `PYTHONPATH=src python3 -m omi --version` printed "omi 0.3.2". `.omi/version` reads 0.3.2, and pyproject.toml and the README are bumped. The new 0.3.2 entry in template_shas.json has 62 files and equals `omi.upgrade.template_shas()` exactly.
> AC: All tests pass on the Linux worker and the Windows host. ✓ for the Linux worker: `python3 tests/test_omi.py` exited 0. HOST for the Windows host part: it can't run in this container, so it does not block PASS.
> ```

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-haiku-5-5 | low | 22 | 3410 | 373974 | 266s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 10 | 1338 | 129920 | 248s | - | PASS d61e676 |
