---
id: TASK-070
title: Add plans that group tasks, with progress in omi status
status: in-progress
depends: TASK-069
scope: src/omi/__init__.py, tests/**, src/omi/template/**, .omi/plans/**, .omi/tasks/_template.md, AGENTS.md
role: omi-agent-engineer
skills: []
tool: codex  # PO: try codex on simpler tasks
workflow: omi-flow-feature
step: build
---
## Goal
Plans in `.omi/plans/PLAN-NNN.md` (frontmatter `id, title, status: active|done`, then goal and done criteria) group tasks that set `plan: PLAN-NNN`; `omi status` shows each active plan's progress. Spec: `docs/specs/template-kinds.md` (Plans).

## Acceptance criteria
- [ ] `python -m omi plans` validates each plan (id = file name, title, status in active|done) and writes `.omi/plans/CATALOG.md`.
- [ ] A task whose `plan` names an unknown plan fails `omi run` with a clear message. Tested.
- [ ] `omi status` prints one line per active plan: `PLAN-NNN title: done x/y` counted from tasks with that `plan`. Tested.
- [ ] `plan:` is in `.omi/tasks/_template.md` (root and template) and is Coordinator-owned frontmatter.
- [ ] The template ships `PLAN-000.md` (an example) and the catalog; `omi init` creates them. Tested.
- [ ] Template and root `AGENTS.md` mention plans in one line each.
- [ ] All tests pass.

## Checkpoint
Done: Fixed the review finding: status reports each plan validation error, skips malformed plans, and continues showing valid plan progress and task status. Plans catalog generation and run validation still fail hard on invalid plans. Previous TASK-070 acceptance criteria remain implemented.
Not done: None in implementation scope; Coordinator review pending.
Tests: PASS — python3 tests/test_omi.py (exit 0, final output: ok). Regression test covers multiple errors in a malformed plan, valid plan progress, remaining task status, and strict run validation; existing CLI validation tests pass.
Next: Coordinator reviews the fix and completes the review/merge workflow. Suggested commit: fix(plans): keep status available when a plan is invalid.

## Steps
- plan started 2026-10-26 14:05
- plan done 2026-10-26 14:05
- build started 2026-10-26 14:05
- build done 2026-10-26 14:08
- review started 2026-10-26 14:08
- review failed 2026-10-26 14:10
- build started 2026-10-26 14:10

## Reports
2026-10-26 14:05 omi-agent-engineer (codex):
> Tôi sẽ đọc task và skill được chỉ định, triển khai trong phạm vi cho phép, rồi chạy kiểm thử và cập nhật checkpoint.
2026-10-26 14:08 omi-agent-engineer (codex):
> DONE — Đã triển khai TASK-070 và cập nhật checkpoint.
> Files: `src/omi/__init__.py`, `tests/test_omi.py`, root/template `AGENTS.md`, task templates, plan catalogs và `PLAN-000.md` trong template.
> Commit đề xuất: `feat(plans): group tasks and show plan progress in status`
> Tests: `python3 tests/test_omi.py` PASS, exit 0.
> Vấn đề còn mở: Không; chờ Coordinator review. Chưa commit.
2026-10-26 14:09 omi-agent-reviewer (claude):
> VERDICT: PASS
> - src/omi/__init__.py:1797 `check_task_plan(wt, tm)` looks for plans in the task's worktree, but the nearby role lookup uses `main`. A plan the Coordinator created in the main checkout and hasn't committed yet would be reported as an unknown plan. -> Pass `main` instead of `wt`, or confirm that plans are always committed before tasks use them.
> - src/omi/__init__.py:788 `status()` calls `load_plans`, which exits on any invalid plan file. One malformed plan therefore stops `omi status` completely. -> In `status`, report the plan error and keep printing the rest.
> 
> AC: `python -m omi plans` validates plans and writes CATALOG.md ✓ `load_plans` checks id against file name, title, and status. `main` dispatches `plans`. `test_plans` runs the CLI and covers the failure cases, and the catalog is unchanged after a failure.
> AC: A task with an unknown plan fails `omi run` with a clear message ✓ `run_role` calls `check_task_plan` before any worker starts. The test calls `run_role` and asserts "unknown plan PLAN-999" and the plan file path in the message.
> AC: `omi status` prints `PLAN-NNN title: done x/y` for each active plan ✓ The test checks 1/2, 0/0, and that a done plan is not listed.
> AC: `plan:` is in both `_template.md` files and is Coordinator-owned frontmatter ✓ `plan:` is added to the root and template `_template.md` and to `FRONT_OWNED`. The test checks `revert_front` for changed, added, and removed `plan` lines.
> AC: Template ships `PLAN-000.md` and the catalog, and `omi init` creates them ✓ Both files are in `dot-omi/plans`. `plans_catalog` is added to the `init` catalog list, and the test asserts both exist after `init`.
> AC: Template and root `AGENTS.md` each mention plans in one line ✓ Both files get an identical single line.
> AC: All tests pass ✓ `python3 tests/test_omi.py` prints `ok`.
2026-10-26 14:11 omi-agent-engineer (codex):
> DONE — `omi status` báo từng lỗi plan và tiếp tục hiển thị; `omi plans`/`omi run` vẫn từ chối plan lỗi.
> Files: `src/omi/__init__.py`, `tests/test_omi.py`, `.omi/tasks/TASK-070.md` (checkpoint).
> Commit đề xuất: `fix(plans): keep status available when a plan is invalid`
> Tests: `python3 tests/test_omi.py` PASS, exit 0, kết thúc `ok`.
> Vấn đề còn mở: Không; chờ Coordinator review. Chưa commit.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | n/a | n/a | n/a | 31s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 280687 | 4255 | 247552 | 114s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 4 | 1484 | 43354 | 35s | - | PASS 87659a5 |
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 215829 | 1903 | 180736 | 79s | 1/1 omi-skill-lean-implementation | - |
