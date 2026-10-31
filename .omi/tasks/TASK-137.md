---
id: TASK-137
title: omi board reads GitHub omi-state as its only source
status: in-progress
depends: TASK-115
plan: PLAN-007
scope: src/omi/board/**, src/omi/app/cli.py, .omi/rules/omi-modules.md, tests/test_board.py, tests/test_board_server.py, tests/test_board_web.py, tests/test_cli.py, .omi/tasks/TASK-137.md
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
- [x] Before each API read the board runs `git fetch` on the state repo (at most once per 10 s, shared by concurrent requests) and reads files from `origin/main` (e.g. `git show`/`ls-tree` or a read-only worktree), never from uncommitted or unpushed local files; it never pulls, commits, pushes or changes the local working tree.
- [x] Each response carries `source: {"repo": "<origin URL without credentials>", "sha": "<origin/main sha>", "fetched_at": "<time>", "stale": false}`; when fetch fails it serves the last fetched `origin/main` with `stale: true` and the page shows "Dữ liệu cũ - không kết nối được GitHub (lúc <giờ>)".
- [x] No local filesystem path appears in any API response or page; the header shows "github.com/omi-teams/omi-state @ <sha7>".
- [x] Tests with a local bare repo as origin cover: a pushed change appears, a local unpushed change does not, fetch failure gives `stale: true`, and no response contains the state dir path; all tests pass.

## Checkpoint
Done: Fixed all five round-3 findings within the expanded scope. Board startup no longer resolves a project or pulls state; both dispatch and the main CLI entry point have regression coverage for no sync calls. The header uses source.repo with its scheme stripped and sha7. Removed fabricated sync metadata and the clean/ahead/behind UI, retaining the origin/main SHA. Snapshot responses redact literal and resolved cache paths in slash/backslash forms, including nested keys and values. Added board/source.py and its layer to omi-modules.md.
Done: Acceptance criteria remain covered by local bare-origin tests for pushed changes, ignored dirty/unpushed files, unchanged checkout, shared ten-second fetch throttling, stale fallback/recovery, metadata and path-free responses; JavaScript runtime checks cover the dynamic repository header and stale warning. New regressions cover alternate path spellings and absent sync fields/UI.
Not done: No implementation work remains. Optional wheel packaging and real-browser layout/keyboard checks remain unverified because their tools are unavailable.
Tests: python3 tests/test_board.py and python3 tests/test_board_web.py executed and exited 0. python3 tests/test_omi.py executed and exited 0 with final "ok", including board data/server, CLI and JavaScript DOM/runtime tests. Real symlink checks and the simulated symlink permission failure regression ran. Skipped: wheel packaging (pip missing), browser layout/keyboard checks (Playwright missing). Windows host execution unavailable; alternate path separators are covered in the regression.
Next: Coordinator reviews the diff and commits on the host. No commit made.
Session: codex 01a18f84-e0b8-77b2-b9d6-568a0ac29aab

## Steps
- plan started 2026-10-30 22:45
- plan done 2026-10-30 22:45
- build started 2026-10-30 22:45
- build done 2026-10-30 22:58
- review started 2026-10-30 22:58
- review failed 2026-10-30 23:01
- build started 2026-10-30 23:01
- build done 2026-10-30 23:27
- review started 2026-10-30 23:27
- review failed 2026-10-30 23:36
- build started 2026-10-30 23:36

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
2026-10-30 23:19 omi-agent-engineer (codex):
> NEEDS SCOPE: src/omi/app/cli.py - remove startup pull; affected CLI tests identified in checkpoint.
> Changed: tests/test_board.py, .omi/tasks/TASK-137.md.
> Fixed symlink permission handling; added regression coverage.
> Suggested commit: `test(board): guard unavailable snapshot symlinks`
> Tests: `python3 tests/test_omi.py` and `python3 tests/test_board.py` exited 0.
> Skipped: wheel test (pip missing), browser layout/keyboard test (Playwright missing).
> Open issues: startup pull remains; Windows host execution unavailable. No commit made.
2026-10-30 23:24 hook post-run passed:
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
2026-10-30 23:36 omi-agent-reviewer (claude):
> ```
> VERDICT: FAIL
> - src/omi/app/cli.py:190 `omi board` still calls state_sync.pull(project) at startup, so criterion 1 ("never pulls ... or changes the local working tree") is not met -> remove the pull and update tests/test_board_server.py::test_board_cli. The checkpoint defers this to TASK-120, so it needs a scope extension.
> - src/omi/board/web/app.js:525 The header "github.com/omi-teams/omi-state @ sha7" is hard-coded and ignores source.repo -> build it from source.repo (strip the scheme) plus the sha.
> - src/omi/board/data.py:136 The `sync` object is fabricated as ahead 0 / behind 0 / dirty False, so the UI shows "✓ Sạch" without checking anything -> drop the field and its UI, or show only the origin/main sha.
> - src/omi/board/source.py:455 Path redaction only replaces the literal str(self.home), so differently spelled paths in state documents would not be redacted. This is plausible but not reproduced. -> also redact the resolved path and its posix/backslash forms.
> - .omi/rules/omi-modules.md Not updated for the new board/source.py module or for its place in the layer order. The file is outside scope -> update it in a follow-up.
> AC: Fetch before each API read (at most once per 10 s, shared), read from origin/main, never pull/commit/push/touch the working tree ✗ The board data layer does this: it uses fetch, ls-tree and show, throttled to 10 s, and test_shared_fetch passes. But cli.py:190 still pulls at board startup.
> AC: Response carries source {repo, sha, fetched_at, stale}; on fetch failure serve the last fetched origin/main with stale: true and show the Vietnamese stale warning ✓ Covered by test_views and the stale case in the JS test. test_omi.py exited 0.
> AC: No local path in any API response or page; header shows "github.com/omi-teams/omi-state @ <sha7>" ✓ Covered by the path-redaction assertions in test_board.py, test_board_server.py and the JS DOM test. Caveat: the header text is hard-coded (finding 2).
> [... truncated ...]
> ```
2026-10-31 08:18 omi-agent-engineer (codex):
> DONE — all five review findings fixed; checkpoint updated. No commit made.
> Changed: `src/omi/app/cli.py`, `src/omi/board/{data.py,source.py,web/app.js,web/app.css}`.
> Changed: `tests/test_board{,_server,_web}.py`, `.omi/rules/omi-modules.md`, `.omi/tasks/TASK-137.md`.
> Suggested commit: `fix(board): use fetched origin state throughout`
> Tests: `python3 tests/test_omi.py` exited 0, final `ok`; focused board/data/frontend tests also passed.
> Skipped: wheel packaging (pip missing), browser layout/keyboard (Playwright missing).
> Open issues: no implementation blockers; skipped checks remain unverified.
2026-10-31 08:22 hook post-run passed:
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
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 1245068 | 4678 | 1167232 | 336s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 10 | 3021 | 220503 | 366s | - | FAIL 6404eaa |
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 1744907 | 7412 | 1685632 | 316s | 1/1 omi-skill-lean-implementation | - |
