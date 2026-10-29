---
id: TASK-113
title: Board data layer: state to JSON-ready dicts
status: in-progress
depends: TASK-112
plan: PLAN-006
scope: src/omi/board/__init__.py, src/omi/board/data.py, tests/test_board.py, tests/test_omi.py, .omi/rules/omi-modules.md, .omi/rules/CATALOG.md, .omi/tasks/TASK-113.md
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
Backend half of the board: pure functions that read `$OMI_STATE` into dicts for the home page, a project dashboard and a task detail, reusing omi's task, plan and usage parsers.

## Acceptance criteria
- [x] `projects()` lists `projects/*` with active plan progress, task counts by status and the PO-waiting count.
- [x] `project(name)` returns PO-waiting items (open po gate, blocked, next task, `Next:` of in-progress tasks), plans, kanban columns, recent activity from `## Steps`/`## Reports`, latest decisions, usage totals per task and model with review rounds, and sync status (ahead/behind, last commit, dirty).
- [x] `task(name, id)` returns frontmatter, Goal, criteria with ticks, Checkpoint, Steps, Reports, Usage.
- [x] Names and IDs are validated; any resolved path outside `$OMI_STATE` raises; nothing is written.
- [x] `omi-modules` rule places `board` in the layer order (above project/state, below app).
- [x] Tests in tests/test_board.py (run by tests/test_omi.py) on a temporary state repo cover each function and the path refusal; all tests pass.

## Checkpoint
Review round 1 FAIL: tests fail on the Windows host: tests/test_board.py:98/101/106 `symlink_to` raises OSError [WinError 1314] (no symlink privilege). Follow tests/test_init.py:47-53: wrap only the symlink cases in `try: ... except OSError: print("skip board symlink refusal: symlink creation unavailable"); return` (or skip just those cases), keep the invalid name/id refusal checks running unconditionally. Rerun python3 tests/test_omi.py.
Done: Implemented board projects/project/task views, state path validation, waiting items, plans, kanban, activity, decisions, usage, sync, module layer rule and regression tests.
Not done: None.
Tests: python3 tests/test_board.py passed (3 test functions; none skipped), including the final dotted-name/path validation changes. python3 tests/test_omi.py passed (exit 0, final output ok), including test_board.main(). No tests intentionally skipped.
Next: Coordinator reviews the scoped diff and commits on the host.

## Steps
- plan started 2026-10-29 22:05
- plan done 2026-10-29 22:05
- build started 2026-10-29 22:05
- build done 2026-10-29 22:18
- review started 2026-10-29 22:18
- review failed 2026-10-29 22:20
- build started 2026-10-29 22:20

## Reports
2026-10-29 22:11 omi-agent-engineer (codex):
> DONE
> Files: `src/omi/board/{__init__,data}.py`, `tests/test_{board,omi}.py`, `.omi/rules/{omi-modules,CATALOG}.md`, `.omi/tasks/TASK-113.md`.
> Suggested commit: `feat(board): add read-only state data views`
> Tests: `python3 tests/test_board.py` and `python3 tests/test_omi.py` passed; no intentional skips.
> Checkpoint updated. Open issues: none. No commit made.
2026-10-29 22:15 hook post-run passed:
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
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 1109307 | 10176 | 1024384 | 357s | 1/1 omi-skill-lean-implementation | - |
