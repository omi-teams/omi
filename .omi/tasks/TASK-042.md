---
id: TASK-042
title: Opt-in parallel tasks (PO request only)
status: planned
depends: TASK-041, TASK-038
scope: src/omi/__init__.py, src/omi/template/**, .claude/skills/omi-task/**, tests/**, AGENTS.md
---
## Goal
Run independent tasks in parallel only when the PO asks, with conflicts caught by code.

## Acceptance criteria
- [ ] `omi-task <ID> <ID>` (or a PO request) starts several tasks only when their `depends` and `scope` globs do not overlap; overlap fails with the paths.
- [ ] Each task gets its own worktree, container name and usage record; `omi clean` removes them all.
- [ ] Default stays one task at a time; AGENTS.md grows by at most 1 line.
- [ ] `python tests/test_omi.py` passes, including an overlap test.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-039
