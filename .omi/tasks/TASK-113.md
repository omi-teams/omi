---
id: TASK-113
title: Board data layer: state to JSON-ready dicts
status: done
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
step: review
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
Host: python tests/test_omi.py -> ok (exit 0, Windows; symlink refusal cases skipped: no symlink privilege)
Done: Fixed review round 1 Windows portability failure. Each of the three symlink creation sites in tests/test_board.py catches OSError, prints "skip board symlink refusal: symlink creation unavailable", and returns. Invalid-name/id refusal checks always run first; refusal assertions and other filesystem operations remain outside the handlers. Existing board implementation and acceptance coverage retained.
Not done: None.
Tests: python3 tests/test_board.py passed (3 test functions, no skips). python3 tests/test_omi.py passed (exit 0, final output ok), including test_board.main(). Additional inline regression checks simulated OSError at symlink creation calls 1, 5 and 6: all three handlers printed the expected skip message, and all six invalid-name/id checks ran before each simulated skip. Only the remaining symlink cases were skipped in those simulations; normal board tests skipped none.
Next: Coordinator reviews the scoped diff and commits on the host. Native Windows rerun remains for the Coordinator; privilege failure was simulated in this container.

## Steps
- plan started 2026-10-29 22:05
- plan done 2026-10-29 22:05
- build started 2026-10-29 22:05
- build done 2026-10-29 22:18
- review started 2026-10-29 22:18
- review failed 2026-10-29 22:20
- build started 2026-10-29 22:20
- build done 2026-10-29 22:31
- review started 2026-10-29 22:31

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
2026-10-29 22:25 omi-agent-engineer (codex):
> DONE
> Files changed: `tests/test_board.py`, `.omi/tasks/TASK-113.md`.
> Fixed symlink privilege handling; invalid-name/ID checks always run. Checkpoint updated.
> Suggested commit: `test(board): handle unavailable symlink creation`
> Tests: board tests and full `python3 tests/test_omi.py` passed; board tests skipped none.
> Simulated privilege failures passed at all three creation sites, skipping remaining symlink cases.
> Open issues: native Windows rerun remains for Coordinator. No commit made.
2026-10-29 22:29 hook post-run passed:
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
2026-10-29 22:39 omi-agent-reviewer (claude):
> VERDICT: PASS
> - src/omi/board/data.py:341 `project()` and `_waiting()` raise `ValueError` when a task filename or a `workflow:` value fails the strict id regex. One odd file then breaks the whole dashboard and `projects()` -> skip invalid entries instead of raising. Not blocking; the repo's real task and workflow files all pass the regex.
> - tests/test_board.py:483 When symlink creation fails (Windows without the privilege), the test returns early. That skips every remaining path-escape case while still reporting success. This was an explicit fix for review round 1 -> acceptable, but the escape-refusal criterion is only partly covered on such hosts.
> 
> AC: `projects()` lists projects with active plan progress, task counts by status and PO-waiting count ✓ `test_views` asserts the full `projects()` output, and `python3 tests/test_omi.py` exits 0 ("ok").
> AC: `project(name)` returns PO-waiting items, plans, kanban, activity, decisions, usage per task and model with review rounds, and sync status ✓ `test_views` asserts each of these, including ahead 1, behind 1 and dirty.
> AC: `task(name, id)` returns frontmatter, Goal, criteria with ticks, Checkpoint, Steps, Reports, Usage ✓ `test_views` asserts each field.
> AC: Names and IDs are validated; any resolved path outside `$OMI_STATE` raises; nothing is written ✓ `test_path_refusal` checks invalid names and the symlink escapes, and `test_views` compares file bytes before and after. On this host symlink creation worked, so none of the cases were skipped.
> AC: `omi-modules` rule places `board` in the layer order ✓ `app.cli > board.data > setup.* …` is in the rule, and `test_empty_and_layer` asserts the order.
> AC: Tests in tests/test_board.py (run by tests/test_omi.py) on a temporary state repo cover each function and the path refusal; all tests pass ✓ `test_board.main()` is wired into tests/test_omi.py. `python3 tests/test_board.py` exits 0 and the full suite ends with "ok".

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 1109307 | 10176 | 1024384 | 357s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 1162801 | 3535 | 1102208 | 299s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 16 | 3329 | 295000 | 316s | - | PASS ef448d3 |
