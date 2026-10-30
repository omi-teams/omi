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
Review round 2 FAIL:
- Host tests (Windows, no symlink privilege) crash in tests/test_board.py (new tests around lines 207-215) with `OSError: [WinError 1314]` from `target.symlink_to(...)`. Guard like the existing tests on development (tests/test_board.py:125-145): wrap the symlink creation in `try/except OSError`, print `skip board snapshot symlink: symlink creation unavailable` and skip only that check. Round 1 drive-path fix is verified on the host.
- Still out of this round: the `state_sync.pull` removal in src/omi/app/cli.py (cli.py is in TASK-120's scope; widened after TASK-120 merges).
Done: Review round 1 Windows path leak fixed in src/omi/board/source.py::_repo: a drive letter followed by :/ or :\ returns an empty repo value before scp-like remote parsing. Added C:\x\y and C:/x/y regression cases in tests/test_board.py; credential sanitization and valid remote cases remain covered.
Done: Existing tests cover fetched origin/main data, pushed changes, ignored local dirty/unpushed changes, concurrent 10-second fetch throttling, failed fetch and recovery, unchanged checkout, API path redaction, source metadata, header and stale warning.
Not done: Criterion 1 remains incomplete end to end because src/omi/app/cli.py:190 still calls state_sync.pull(project) at board startup. The task explicitly defers that file to parallel TASK-120; it was not modified. Checked affected tests: tests/test_board_server.py::test_board_cli expects one pull and must change alongside removal; tests/test_cli.py::test_cli_characterization covers board dispatch.
Tests: python3 tests/test_omi.py executed and exited 0 with final "ok", including board data/server tests, both Windows drive path cases and JavaScript DOM/runtime checks. Skipped: test_wheel_ships_web (pip missing); test_browser_layout_and_keyboard (Playwright missing). Windows host execution was not available; Windows path strings were tested on this container.
Next: Coordinator reviews the scoped fix, extends scope to src/omi/app/cli.py after TASK-120 merges, removes the board startup pull, updates the existing CLI assertion, and reruns python3 tests/test_omi.py. No commit made.

## Steps
- plan started 2026-10-30 22:45
- plan done 2026-10-30 22:45
- build started 2026-10-30 22:45
- build done 2026-10-30 22:58
- review started 2026-10-30 22:58
- review failed 2026-10-30 23:01
- build started 2026-10-30 23:01

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
2026-10-30 23:07 omi-agent-engineer (codex):
> NEEDS SCOPE: src/omi/app/cli.py - remove startup pull to complete criterion 1; update existing board CLI test.
> Changed: src/omi/board/source.py, tests/test_board.py, .omi/tasks/TASK-137.md.
> Fixed Windows drive-path leak; added both regression cases; checkpoint updated.
> Suggested commit: `fix(board): reject Windows drive paths in source metadata`
> Tests: `python3 tests/test_omi.py` exited 0, final `ok`; DOM/runtime checks ran.
> Skipped: wheel test (pip missing), browser layout/keyboard test (Playwright missing).
> Open issue: startup pull remains; no commit made.
2026-10-30 23:13 hook post-run passed:
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
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 990160 | 3031 | 920320 | 366s | 1/1 omi-skill-lean-implementation | - |
