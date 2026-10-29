---
id: TASK-099
title: State sync: auto pull/commit/push and omi sync
status: in-progress
depends: TASK-098
plan: PLAN-004
scope: src/omi/*.py, tests/test_omi.py, README.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature
step: build
---
## Goal
Several machines share one omi-state repo without the PO running git by hand.

## Acceptance criteria
- [x] `omi status` in a detached project runs `git pull --rebase` on the state repo first (skipped with a one-line note when offline or no remote). Tested with a local bare remote.
- [x] Every command that changes state (`step`, task start/done, decisions, plans, `omi run` reports/usage) commits only the files it changed in the state repo (`chore(<project>): <what>`) and pushes; a push failure prints `STATE NOT PUSHED: run omi sync` and keeps the commit. Tested.
- [x] `omi sync` pulls, commits any leftover state change and pushes; a rebase conflict stops with the file list and changes nothing more. Tested.
- [x] `omi sync` is listed in USAGE and pinned in `test_cli_characterization` (exit codes and key output).
- [ ] All tests pass on the Linux worker and the Windows host; in-repo mode behaviour is unchanged (existing tests untouched or only extended).

## Checkpoint
Done: Added detached status pull, per-command commits/pushes, omi sync recovery/conflict handling, README and bare-remote/CLI/report tests. In-repo behavior preserved.
Not done: Windows host execution (Linux worker only).
Tests: Final python3 tests/test_omi.py executed all listed tests on Linux, exit 0 (ok). Includes local bare-remote pull/push, selective commits, reports/usage, offline/no-remote, failed-push recovery, leftovers/deletions, upstream setup, rebase conflict preservation and CLI characterization. Windows-only execution was not run.
Next: Coordinator reviews diff and runs python3 tests/test_omi.py on Windows before committing. No worktree commit made.

## Steps
- plan started 2026-10-29 10:10
- plan done 2026-10-29 10:10
- build started 2026-10-29 10:10

## Reports
2026-10-29 10:18 omi-agent-engineer (codex):
> DONE
> Files: `src/omi/cli.py`, `src/omi/state_sync.py`, `tests/test_omi.py`, `README.md`, `.omi/tasks/TASK-099.md`.
> Suggested commit: `feat(state): automatically sync detached project state`
> Tests: `python3 tests/test_omi.py` passed on Linux (exit 0).
> Open: Windows host verification pending. Checkpoint updated; no commit made.
2026-10-29 10:21 hook post-run passed:
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
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 2407656 | 15168 | 2327168 | 507s | 1/1 omi-skill-lean-implementation | - |
