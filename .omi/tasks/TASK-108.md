---
id: TASK-108
title: Warn when an attached repo still has in-repo omi files
status: done
depends: TASK-118
plan: PLAN-005
scope: src/omi/upgrade.py, src/omi/cli.py, tests/test_attach.py, .omi/tasks/TASK-108.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature
step: accept
---
## Goal
Pilot gap G4: the PO sees that in-repo `.omi/`, `AGENTS.md` or `.claude/` in an attached code repo are ignored.

## Acceptance criteria
- [x] `omi attach` and `omi status` in detached mode print one `WARN: in-repo omi files ignored (detached): <paths>` line when the code repo tracks `.omi/`, `AGENTS.md` or `.claude/`; nothing is printed otherwise; no migration.
- [x] In-repo mode output is unchanged.
- [x] Tests in tests/test_attach.py cover warn and no-warn cases; README is left to TASK-110; all tests pass.

## Checkpoint
Host: python tests/test_omi.py (Windows host, worktree) -> ok, exit 0
Done: Shared tracked-path warning for attach (new/existing registration) and detached status; warn/no-warn, no-migration and in-repo output tests added. README unchanged.
Not done: None within scope.
Tests: python3 tests/test_attach.py passed (exit 0); python3 tests/test_omi.py passed (exit 0, final output ok). Both commands executed tests; no task tests skipped.
Next: Coordinator reviews the diff and commits on the host.

## Steps
PO approval accept: Chấp nhận, merge
- plan started 2026-10-29 16:07
- plan done 2026-10-29 16:07
- build started 2026-10-29 16:07
- build done 2026-10-29 16:17
- review started 2026-10-29 16:17
- review done 2026-10-29 16:23
- accept started 2026-10-29 16:23
- accept done 2026-10-29 16:23

## Reports
2026-10-29 16:12 omi-agent-engineer (codex):
> DONE
> Files changed: `src/omi/upgrade.py`, `src/omi/cli.py`, `tests/test_attach.py`, `.omi/tasks/TASK-108.md`.
> Suggested commit: `fix: warn about tracked in-repo omi files in detached mode`
> Tests: `python3 tests/test_attach.py` and `python3 tests/test_omi.py` passed (exit 0).
> Checkpoint updated; README unchanged; no commit created.
> Open issues: none.
2026-10-29 16:16 hook post-run passed:
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
2026-10-29 16:23 omi-agent-reviewer (codex):
> VERDICT: PASS
> AC: Detached attach/status print exactly one warning for tracked omi paths, otherwise none; no migration ✓ Real-Git warn/no-warn tests passed; file contents and staged changes preserved.
> AC: In-repo mode output unchanged ✓ test_in_repo_status_unchanged passed.
> AC: tests/test_attach.py covers warn/no-warn; README unchanged; all tests pass ✓ Both python3 tests/test_attach.py and python3 tests/test_omi.py exited 0; full suite ended with “ok”; README absent from diff.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 1060930 | 4605 | 1012352 | 337s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | gpt-6.1-sol (codex) | medium | 676060 | 2164 | 642304 | 267s | - | PASS b70058e |
