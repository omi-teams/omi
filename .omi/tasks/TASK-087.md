---
id: TASK-087
title: omi run excludes .omi-cache/ via the repo's info/exclude when .gitignore lacks it
status: in-progress
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
step: build
---
## Goal
Follow-up to TASK-086 review: in a project not yet upgraded (`.gitignore` lacks `.omi-cache/`), download-cache files show as untracked and paths like `.omi-cache/go-mod/x@v1/.github/...` trip the `.git*` scope guard. PO decision 2026-10-27: `omi run` adds `.omi-cache/` to the repo's shared `info/exclude` (`git rev-parse --git-common-dir`) when missing, so every worktree ignores it without a tracked change.

## Acceptance criteria
- [x] Before any role or hook container starts, `omi run` ensures the line `.omi-cache/` exists in `<git-common-dir>/info/exclude` (creates the file/dir if missing, no duplicate on repeat runs, keeps existing lines). Tested.
- [x] In a repo whose `.gitignore` has no `.omi-cache/`, an untracked `.omi-cache/go-mod/example.com/m@v1/.github/workflows/x.yml` in the task worktree is not reported by `out_of_scope` after that step; a committed file under `.omi-cache/` is still out of scope. Tested with real git (worktree created via `git worktree add`).
- [x] No tracked file changes from this step (`git status --porcelain` of the main checkout and the worktree unchanged). Tested.
- [ ] All tests pass on the Linux worker and the Windows host.

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

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 1633186 | 7391 | 1544448 | 450s | 1/1 omi-skill-lean-implementation | - |
