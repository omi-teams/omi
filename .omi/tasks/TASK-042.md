---
id: TASK-042
title: Opt-in parallel tasks (PO request only)
status: done
depends: TASK-041, TASK-038
scope: src/omi/__init__.py, src/omi/template/**, .claude/skills/omi-task/**, tests/**, AGENTS.md
role: omi-agent-engineer
skills: []  # step build adds omi-skill-lean-implementation
workflow: omi-flow-feature
step: accept
---
## Goal
Run independent tasks in parallel only when the PO asks, with conflicts caught by code.

### Brief
- New command `python -m omi parallel <ID> <ID> [...]` in `src/omi/__init__.py` (add to the usage text and `main`): exits 1 listing every conflict, else prints `parallel ok: <IDs>`. Conflicts: one task in another's `depends` (direct or transitive, via the task files), a task not `planned`/`in-progress`, or two tasks whose `scope` globs can match the same path. Glob overlap: compare the literal part before the first `*`, `?` or `[` of each glob; overlap when one is a prefix of the other on a `/` boundary or they are equal (`ponytail:` comment naming the ceiling: may report a false overlap, never misses one).
- Check (no new code expected, test it): `container_name` includes the task id, each task has its own worktree in `task_worktrees`, `record_usage` writes the task's own file, `omi clean` removes containers of all tasks.
- `.claude/skills/omi-task/SKILL.md` (root and template, identical, net growth at most 2 lines): `omi-task <ID> <ID>` only when the PO asks; run `python -m omi parallel <IDs>` first and stop with its output on a conflict; then run each task's steps, engineers in background (`run_in_background`), one PO accept question per task.
- AGENTS.md: keep the existing "One task at a time unless the PO asks for parallel work." line; at most 1 more line (root and template identical).
- Tests: `python3 tests/test_omi.py`; cases: disjoint scopes ok, overlapping globs fail with both globs, depends fail, status done fail.

## Acceptance criteria
- [x] `omi-task <ID> <ID>` (or a PO request) starts several tasks only when their `depends` and `scope` globs do not overlap; overlap fails with the paths.
- [x] Each task gets its own worktree, container name and usage record; `omi clean` removes them all.
- [x] Default stays one task at a time; AGENTS.md grows by at most 1 line.
- [x] `python tests/test_omi.py` passes, including an overlap test.

## Checkpoint
Done: omi parallel (+usage), SKILL.md, AGENTS.md; review round 1 fixes: worktrees/usage/clean tests (clean label test already in test_clean_and_old_images), main wiring tests, if/exit in main, duplicate id check + test
Not done: -
Tests: python3 tests/test_omi.py ok
Next: review

## Steps
- plan started 2026-10-25 22:51
- plan done 2026-10-25 22:51
- build started 2026-10-25 22:51
- build done 2026-10-25 22:53
- review started 2026-10-25 22:53
- review failed 2026-10-25 22:54
- build started 2026-10-25 22:54
- build done 2026-10-25 22:55
- review started 2026-10-25 22:55
- review done 2026-10-25 22:56
- accept started 2026-10-25 22:56
PO approval accept: Chấp nhận, merge (Recommended)
- accept done 2026-10-25 22:56

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 18 | 4691 | 242055 | 60s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 2502 | 68311 | 35s | - | FAIL 5d0e4d3 |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 16 | 2821 | 202216 | 64s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 1922 | 70028 | 30s | - | PASS 676eedf |
