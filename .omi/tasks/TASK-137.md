---
id: TASK-137
title: omi board reads GitHub omi-state as its only source
status: in-progress
depends: TASK-115
plan: PLAN-007
scope: src/omi/board/**, tests/test_board.py, tests/test_board_server.py, tests/test_board_web.py, .omi/tasks/TASK-137.md
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
Every board refresh shows exactly what is on `origin/main` of the GitHub omi-state repo; the local clone is only a read-only cache and its path is never shown.

## Acceptance criteria
- [ ] Before each API read the board runs `git fetch` on the state repo (at most once per 10 s, shared by concurrent requests) and reads files from `origin/main` (e.g. `git show`/`ls-tree` or a read-only worktree), never from uncommitted or unpushed local files; it never pulls, commits, pushes or changes the local working tree.
- [ ] Each response carries `source: {"repo": "<origin URL without credentials>", "sha": "<origin/main sha>", "fetched_at": "<time>", "stale": false}`; when fetch fails it serves the last fetched `origin/main` with `stale: true` and the page shows "Dữ liệu cũ - không kết nối được GitHub (lúc <giờ>)".
- [ ] No local filesystem path appears in any API response or page; the header shows "github.com/omi-teams/omi-state @ <sha7>".
- [ ] Tests with a local bare repo as origin cover: a pushed change appears, a local unpushed change does not, fetch failure gives `stale: true`, and no response contains the state dir path; all tests pass.

## Checkpoint
Done: Scoped board implementation reads immutable fetched origin/main blobs; concurrent requests share a 10-second fetch throttle; responses include sanitized source metadata; stale snapshots and Vietnamese warning are supported; local cache paths are removed. Added bare-origin integration, concurrency, failure/recovery, API and frontend runtime coverage.
Not done: Criterion 1 remains incomplete end to end: src/omi/app/cli.py:190 still calls state_sync.pull(project) on board startup, outside this task's scope. Existing tests/test_board_server.py::test_board_cli explicitly expects that pull and must change alongside its removal; tests/test_cli.py dispatch coverage is also affected.
Tests: python3 tests/test_board.py, python3 tests/test_board_server.py, and python3 tests/test_board_web.py executed successfully. JavaScript DOM/runtime checks executed. Wheel test skipped (pip missing); browser layout/keyboard test skipped (Playwright missing). python3 tests/test_omi.py completed with exit 0 (final ok); the focused board tests were rerun successfully after the final code/test edits. The same wheel and browser checks were skipped in the full suite.
Next: Coordinator must extend scope to src/omi/app/cli.py; remove the board startup pull, update tests/test_board_server.py::test_board_cli to assert no pull, and rerun python3 tests/test_omi.py. Scoped work is ready for review; no commit made.

## Steps
- plan started 2026-10-30 22:45
- plan done 2026-10-30 22:45
- build started 2026-10-30 22:45

## Reports
2026-10-30 22:53 omi-agent-engineer (codex):
> NEEDS SCOPE: src/omi/app/cli.py - remove the board startup pull to satisfy criterion 1.
> Changed: board data/source, web JS/CSS/HTML, three board test files, TASK-137 checkpoint.
> Suggested commit: `fix(board): read state from fetched origin/main`
> Tests: `python3 tests/test_omi.py` exited 0; focused board tests passed.
> Skipped: wheel test (pip missing), browser checks (Playwright missing).
> Open issue: startup pull and its existing test expectation remain; no commit made.
2026-10-30 22:57 hook post-run passed:
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
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 1862645 | 13715 | 1792768 | 457s | 1/1 omi-skill-lean-implementation | - |
