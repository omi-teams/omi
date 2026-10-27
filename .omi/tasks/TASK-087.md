---
id: TASK-087
title: omi run excludes .omi-cache/ via the repo's info/exclude when .gitignore lacks it
status: done
depends: TASK-086
plan: PLAN-001
scope: src/omi/__init__.py, tests/test_omi.py
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: sonnet
effort: medium
workflow: omi-flow-feature
step: review
---
## Goal
Follow-up to TASK-086 review: in a project not yet upgraded (`.gitignore` lacks `.omi-cache/`), download-cache files show as untracked and paths like `.omi-cache/go-mod/x@v1/.github/...` trip the `.git*` scope guard. PO decision 2026-10-27: `omi run` adds `.omi-cache/` to the repo's shared `info/exclude` (`git rev-parse --git-common-dir`) when missing, so every worktree ignores it without a tracked change.

## Acceptance criteria
- [x] Before any role or hook container starts, `omi run` ensures the line `.omi-cache/` exists in `<git-common-dir>/info/exclude` (creates the file/dir if missing, no duplicate on repeat runs, keeps existing lines). Tested.
- [x] In a repo whose `.gitignore` has no `.omi-cache/`, an untracked `.omi-cache/go-mod/example.com/m@v1/.github/workflows/x.yml` in the task worktree is not reported by `out_of_scope` after that step; a committed file under `.omi-cache/` is still out of scope. Tested with real git (worktree created via `git worktree add`).
- [x] No tracked file changes from this step (`git status --porcelain` of the main checkout and the worktree unchanged). Tested.
- [x] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done: Added shared info/exclude cache setup before role checks and containers; covered missing directory/file, preserved lines, repeat runs, real linked-worktree scope checks, and unchanged checkout statuses.
Not done: -
Coordinator: Windows host suite passed (ok).
Tests: PASS - TMPDIR=/work PYTHONDONTWRITEBYTECODE=1 python3 tests/test_omi.py (Linux, Python 3.13.5; exit 0, ok), including real Git linked-worktree regression and container ordering checks. Windows host run pending.
Next: Coordinator reviews diff and runs python3 tests/test_omi.py on Windows. After merge: omi-release 0.3.0.

## Steps
- plan started 2026-10-27 22:06
- plan done 2026-10-27 22:06
- build started 2026-10-27 22:06
- build done 2026-10-27 22:17
- review started 2026-10-27 22:17
- review done 2026-10-27 22:22

## Reports
2026-10-27 22:14 omi-agent-engineer (codex):
> DONE — Shared cache exclusion runs before role checks and containers.
> Files changed: `src/omi/__init__.py`, `tests/test_omi.py`, `.omi/tasks/TASK-087.md`.
> Suggested commit: `fix(run): exclude download cache through shared git info/exclude`
> Tests: Full Linux suite passed (exit 0), including real Git worktree regressions.
> Open issues: Windows host validation pending; checkpoint updated.
2026-10-27 22:16 hook post-run passed:
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
2026-10-27 22:22 omi-agent-reviewer (claude):
> ```
> VERDICT: PASS
> - src/omi/__init__.py:1793 `omi hook` (hook_cmd) calls run_hook directly and never calls ensure_cache_excluded, so a hook container started that way can run in a repo whose exclude is not yet set up. The AC covers `omi run` only, so this is minor -> call ensure_cache_excluded(wt) in hook_cmd before run_hook.
> AC: Before any container, `omi run` ensures `.omi-cache/` is in <common-dir>/info/exclude ✓ ensure_cache_excluded runs at src/omi/__init__.py:2320, before the pre-run hook at 2329 and the role container. It creates the directory and file, appends only when the line is missing, and keeps existing lines. test_download_cache_shared_exclude covers the missing dir, missing file, preserved lines, and repeat runs. The docker-run mocks in test_hooks and test_run_read_role assert the exclude file exists with exactly one entry when the container starts.
> AC: An untracked .omi-cache/.../.github/... file is not reported by out_of_scope, and a committed cache file still is ✓ The test uses a real `git worktree add`. out_of_scope returns the cache path before the call and [] after. After `git add -f` and a commit, it reports the path again, both committed and uncommitted.
> AC: No tracked file changes ✓ The test asserts `git status --porcelain -uall` is unchanged for both the main checkout and the worktree.
> AC: All tests pass on the Linux worker and the Windows host ✓ (partial) `python3 tests/test_omi.py` exits 0 and prints "ok" on Linux in this container. The Windows pass is only the coordinator's note in the task file, and I did not re-run it.
> ```

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 1633186 | 7391 | 1544448 | 450s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 10 | 1472 | 128367 | 247s | - | PASS 21b12b4 |
