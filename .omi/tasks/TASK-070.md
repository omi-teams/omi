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
Done: Implemented plan validation/catalog CLI, unknown task plan rejection before worker startup, active plan progress (including 0/0), Coordinator-owned plan frontmatter, root/template instructions, and PLAN-000 example/catalog installed by init. Added tests for all acceptance criteria.
Not done: None in implementation scope; Coordinator review pending.
Tests: PASS — python3 tests/test_omi.py (exit 0, final output: ok).
Next: Coordinator reviews diff and runs the review workflow; suggested commit: feat(plans): group tasks and show plan progress in status.

## Steps
- plan started 2026-10-26 14:05
- plan done 2026-10-26 14:05
- build started 2026-10-26 14:05

## Reports
2026-10-26 14:05 omi-agent-engineer (codex):
> Tôi sẽ đọc task và skill được chỉ định, triển khai trong phạm vi cho phép, rồi chạy kiểm thử và cập nhật checkpoint.
2026-10-26 14:08 omi-agent-engineer (codex):
> DONE — Đã triển khai TASK-070 và cập nhật checkpoint.
> Files: `src/omi/__init__.py`, `tests/test_omi.py`, root/template `AGENTS.md`, task templates, plan catalogs và `PLAN-000.md` trong template.
> Commit đề xuất: `feat(plans): group tasks and show plan progress in status`
> Tests: `python3 tests/test_omi.py` PASS, exit 0.
> Vấn đề còn mở: Không; chờ Coordinator review. Chưa commit.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | n/a | n/a | n/a | 31s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 280687 | 4255 | 247552 | 114s | 1/1 omi-skill-lean-implementation | - |
