---
id: TASK-069
title: Add references a task names with refs, passed to agents as paths
status: done
depends: TASK-068
scope: src/omi/__init__.py, tests/**, src/omi/template/**, .omi/references/**, .omi/tasks/_template.md, AGENTS.md
role: omi-agent-engineer
skills: []
tool: codex  # PO: try codex on simpler tasks
workflow: omi-flow-feature
step: accept
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
PO approval accept: Nghiệm thu + thêm vào 072 (Recommended)
- plan started 2026-10-26 13:55
- plan done 2026-10-26 13:55
- build started 2026-10-26 13:55
- build done 2026-10-26 14:01
- review started 2026-10-26 14:01
- review done 2026-10-26 14:02
- accept started 2026-10-26 14:02
- accept done 2026-10-26 14:03

## Reports
2026-10-26 13:58 omi-agent-engineer (codex):
> DONE — Hoàn thành TASK-069, đã cập nhật checkpoint.
> Tệp sửa: `src/omi/__init__.py`, `tests/test_omi.py`, task template và `AGENTS.md` ở root/template, references cùng catalog ở root/template, task TASK-069.
> Commit đề xuất: `feat: add task references and validate selected rules`
> Tests: `python3 tests/test_omi.py` PASS, exit 0, kết thúc `ok`.
> Vấn đề còn mở: không. Chưa commit; chờ Coordinator review.
2026-10-26 14:01 omi-agent-reviewer (codex):
> VERDICT: PASS
> AC: CLI xác thực id/summary và sinh catalog ✓ test_references.
> AC: Prompt chứa đường dẫn refs; chặn ref lạ hoặc thiếu catalog ✓ test_rules.
> AC: refs có trong hai task template và thuộc Coordinator ✓ test_references kiểm tra revert_front.
> AC: Template cung cấp hai references và catalog; init tạo đủ ✓ test_references, test_init_fresh_project.
> AC: AGENTS.md root/template có dòng references ✓ test_references.
> AC: Chặn rule/ref sai id hoặc thiếu summary; dùng onexc ✓ test_rules.
> AC: Tất cả tests pass ✓ python3 tests/test_omi.py, exit 0, kết thúc “ok”.
2026-10-26 14:02 omi-agent-reviewer (claude):
> VERDICT: PASS
> - tests/test_omi.py: `test_references` doesn't check the scenario where a ref is invalid and the catalog is missing. Coverage is otherwise complete, so this is minor. -> No fix needed.
> - src/omi/__init__.py:75: `parse` cuts a `summary` at the first `#`, so a reference summary like "C# conventions" would be truncated. This behaviour was already there. -> Optional: handle it later, not in this task.
> 
> AC: `python -m omi references` validates each reference and writes the catalog ✓ `references_catalog` checks id against file name and the summary, then exits non-zero without touching the catalog. `test_references` runs the CLI and gets "2 references"; with bad ids and a missing summary it fails and leaves the catalog unchanged.
> AC: `omi run` adds ref paths under "References (read when needed)" and stops on an unknown or uncataloged ref ✓ `task_references` and `reference_prompt` are called from `run_role`. `test_rules` checks the prompt text and that `docker run` is not called for unknown, uncataloged and invalid refs. A 30KB reference body stays out of the prompt, so no budget applies. A `../` id can't traverse because lookup goes through the stem dict.
> AC: `refs:` is in both `_template.md` files and is Coordinator-owned ✓ the diff adds the line to both templates and `"refs"` to `FRONT_OWNED`. The test confirms `revert_front` reverts both changed and newly added `refs`.
> AC: The template ships both references and the catalog, and `omi init` creates them ✓ the files are under `dot-omi/references`. `init` now calls `references_catalog`, and `test_init_fresh_project` and `test_references` check the result.
> AC: Template and root `AGENTS.md` each get one line ✓ the same line is added to both and the test checks for it.
> [... truncated ...]
> Scope ✓ the only file changed outside the listed scope is the task file itself, which is expected.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | codex-default (codex) | medium | 370946 | 4933 | 338944 | 160s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | gpt-6.1-sol (codex) | medium | 142614 | 659 | 113664 | 42s | - | PASS d7105b5 |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 1667 | 80568 | 38s | - | PASS d7105b5 |
