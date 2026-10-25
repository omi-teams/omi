---
id: TASK-042
title: Opt-in parallel tasks (PO request only)
status: in-progress
depends: TASK-041, TASK-038
scope: src/omi/__init__.py, src/omi/template/**, .claude/skills/omi-task/**, tests/**, AGENTS.md
role: omi-agent-engineer
skills: []  # step build adds omi-skill-lean-implementation
workflow: omi-flow-feature
step: build
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
- [ ] `omi-task <ID> <ID>` (or a PO request) starts several tasks only when their `depends` and `scope` globs do not overlap; overlap fails with the paths.
- [ ] Each task gets its own worktree, container name and usage record; `omi clean` removes them all.
- [ ] Default stays one task at a time; AGENTS.md grows by at most 1 line.
- [ ] `python tests/test_omi.py` passes, including an overlap test.

## Checkpoint
Review round 1 FAIL:
1. tests/test_omi.py: add tests: two `task/*` worktrees map to two paths in `task_worktrees`; `record_usage` on TASK-A leaves TASK-B untouched; `clean` selects containers by repo label, not task id (stub `subprocess.run`).
2. tests/test_omi.py: test `main(["parallel", ...])` wiring: exit 1 with conflicts on stderr, `parallel ok: <IDs>` on success, a single ID falls through to usage.
3. src/omi/__init__.py:1439: replace `sys.exit(... else print(...))` with `if conflicts: sys.exit(...)` then `print(...)`.
4. src/omi/__init__.py:538: dedupe IDs, or report `duplicate id`; test it.
Done: omi parallel (+usage), tests, SKILL.md, AGENTS.md (root+template)
Not done: -
Tests: python3 tests/test_omi.py ok
Next: TASK-039

## Steps
- plan started 2026-10-25 22:51
- plan done 2026-10-25 22:51
- build started 2026-10-25 22:51
- build done 2026-10-25 22:53
- review started 2026-10-25 22:53
- review failed 2026-10-25 22:54
- build started 2026-10-25 22:54

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 18 | 4691 | 242055 | 60s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 2502 | 68311 | 35s | - | FAIL 5d0e4d3 |
