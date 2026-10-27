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
step:
---
## Goal
Follow-up to TASK-086 review: in a project not yet upgraded (`.gitignore` lacks `.omi-cache/`), download-cache files show as untracked and paths like `.omi-cache/go-mod/x@v1/.github/...` trip the `.git*` scope guard. PO decision 2026-10-27: `omi run` adds `.omi-cache/` to the repo's shared `info/exclude` (`git rev-parse --git-common-dir`) when missing, so every worktree ignores it without a tracked change.

## Acceptance criteria
- [ ] Before any role or hook container starts, `omi run` ensures the line `.omi-cache/` exists in `<git-common-dir>/info/exclude` (creates the file/dir if missing, no duplicate on repeat runs, keeps existing lines). Tested.
- [ ] In a repo whose `.gitignore` has no `.omi-cache/`, an untracked `.omi-cache/go-mod/example.com/m@v1/.github/workflows/x.yml` in the task worktree is not reported by `out_of_scope` after that step; a committed file under `.omi-cache/` is still out of scope. Tested with real git (worktree created via `git worktree add`).
- [ ] No tracked file changes from this step (`git status --porcelain` of the main checkout and the worktree unchanged). Tested.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next: start with `omi-task TASK-087`. After merge: omi-release 0.3.0.
