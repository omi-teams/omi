---
id: TASK-069
title: Add references a task names with refs, passed to agents as paths
status: in-progress
depends: TASK-068
scope: src/omi/__init__.py, tests/**, src/omi/template/**, .omi/references/**, .omi/tasks/_template.md, AGENTS.md
role: omi-agent-engineer
skills: []
tool: codex  # PO: try codex on simpler tasks
workflow: omi-flow-feature
step: build
---
## Goal
References in `.omi/references/<id>.md` (frontmatter `id, summary`) are listed in a catalog; a task names them with `refs: [...]` and the agent gets their paths to read when needed, outside any budget. Spec: `docs/specs/template-kinds.md` (References).

## Acceptance criteria
- [x] `python -m omi references` validates each reference (id = file name, summary) and writes `.omi/references/CATALOG.md`.
- [x] `omi run` adds the paths of the task's `refs` to the prompt under "References (read when needed)"; an unknown ref or one missing from the catalog stops the run with a clear message. Tested.
- [x] `refs:` is in `.omi/tasks/_template.md` (root and template) and is Coordinator-owned frontmatter like `skills`.
- [x] The template ships references `postgres-conventions` and `nextjs-app-router` and the catalog; `omi init` creates them. Tested.
- [x] Template and root `AGENTS.md` mention references in one line each.
- [x] Carried from TASK-068 review: `omi run` stops when a matched rule or a named ref has validation errors (id, summary), and the test in `test_rules` uses `rmtree(..., onexc=...)` instead of the deprecated `onerror`. Tested.
- [x] All tests pass.

## Checkpoint
Done: Implemented reference validation/catalog CLI, task refs paths in worker prompts, Coordinator-owned refs, root/template documentation and task templates, bundled references and init support. Matched rule validation now blocks invalid rules; test_rules uses onexc. All acceptance criteria covered by tests.
Not done: None within implementation scope; Coordinator review/commit remains.
Tests: PASS — python3 tests/test_omi.py (exit 0, final output: ok). Includes CLI validation, init contents, prompt paths without reference bodies or token limits, unknown/uncataloged/invalid refs, invalid matched rules, and protected refs frontmatter.
Next: Coordinator reviews the diff and proceeds with the workflow; no commit made by the worker.

## Steps
- plan started 2026-10-26 13:55
- plan done 2026-10-26 13:55
- build started 2026-10-26 13:55

## Reports
2026-10-26 13:58 omi-agent-engineer (codex):
> DONE — Hoàn thành TASK-069, đã cập nhật checkpoint.
> Tệp sửa: `src/omi/__init__.py`, `tests/test_omi.py`, task template và `AGENTS.md` ở root/template, references cùng catalog ở root/template, task TASK-069.
> Commit đề xuất: `feat: add task references and validate selected rules`
> Tests: `python3 tests/test_omi.py` PASS, exit 0, kết thúc `ok`.
> Vấn đề còn mở: không. Chưa commit; chờ Coordinator review.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | codex-default (codex) | medium | 370946 | 4933 | 338944 | 160s | 1/1 omi-skill-lean-implementation | - |
