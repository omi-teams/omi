---
id: TASK-134
title: Task phase derived from the current workflow step
status: in-progress
depends: TASK-115
plan: PLAN-006
scope: src/omi/project/**, src/omi/app/cli.py, src/omi/board/data.py, tests/test_omi.py, tests/test_board.py, tests/test_content.py, tests/test_cli.py, .omi/tasks/TASK-134.md
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature
step: build
---
## Goal
At a glance the PO sees which phase and step every task is in, the same set for every workflow, computed from the task's `status`, `step` and workflow definition, with no new field to keep in sync by hand.

## Acceptance criteria
- [ ] One function derives the phase: `status: planned` -> Chưa bắt đầu; `blocked` -> Bị chặn; `done` -> Xong; otherwise from the current step: gate `po` -> Chờ PO; role `coordinator` -> Lên kế hoạch; designer-ui/architect/researcher -> Thiết kế; engineer/docs-writer/devops -> Đang làm; reviewer/security-reviewer -> Đang review; qa-tester -> Đang QA. Unknown role, missing workflow or empty step falls back to Đang làm. Stored task fields and the status enum stay unchanged.
- [ ] Alongside the phase: step position `N/M` with the step id, and the review round (count of review FAIL reports + 1) while in a review or qa step.
- [ ] `omi status` shows `[<phase>] TASK-NNN title` and a second line `bước N/M <step> · vòng R · <tool> <model>/<effort>` plus a compact step strip (done steps ✓, current in brackets), e.g. `plan ✓ design ✓ build ✓ [review] qa · accept`.
- [ ] The board API returns `phase` (stable English key plus Vietnamese label), `step_index`, `step_count` and `review_round` per task (read-only).
- [ ] Tests cover every mapping rule, the fallbacks and the round count; all tests pass.

## Checkpoint
Done: all criteria; updated expected labels in tests/test_content.py and tests/test_cli.py.
Not done: nothing.
Tests: python3 tests/test_omi.py exit 0 (skipped: test_wheel_ships_web, pip missing; browser layout, playwright missing).
Next: review.

## Steps
- plan started 2026-10-30 19:42
- plan done 2026-10-30 19:42
- build started 2026-10-30 19:42

## Reports
2026-10-30 19:52 omi-agent-engineer (claude):
> NEEDS SCOPE: `tests/test_content.py`, `tests/test_cli.py`. The feature is done, but two existing tests still expect the old `[status]` label and now fail.
> - **Failing assertions:** `tests/test_content.py:180` expects `[review] TASK-002`, and `tests/test_cli.py:225,250` expect `[planned] ...`. Those lines should become `[Đang làm]` and `[Chưa bắt đầu]`. A `review`-status task with no step now falls back to Đang làm, as the criteria say.
> - **Files changed:**
>   - `src/omi/project/tasks.py`: `phase`, `review_round` and `step_strip`.
>   - `src/omi/app/cli.py`: status shows the phase label, the `bước N/M …` line and the step strip.
>   - `src/omi/board/data.py`: each task now returns `phase`, `step_index`, `step_count` and `review_round`.
>   - `tests/test_omi.py`: new `test_phase` covering every mapping rule, the fallbacks, the round count and the strip. I added it to this runner's `__main__`.
>   - `tests/test_board.py`: asserts the new board fields.
>   - `.omi/tasks/TASK-134.md`: checkpoint updated.
> - **Suggested commit:** `feat(status): derive task phase, step position and review round from the workflow step`
> - **Test result:** I ran each `tests/test_*.py` file on its own. All passed except `test_content` and `test_cli`, which fail only on the label lines above. `test_upgrade` fails with a missing `pyproject.toml` because I ran it from `tests/`; I did not rerun it from `/work`. The full `python3 tests/test_omi.py` run stops at `test_content`, so it has not passed end to end. `test_phase` and `test_board` passed when run directly.
> - **Open issue:** I kept the ` (step: X)` suffix on the first status line for in-progress tasks. `tests/test_init.py:234` and `tests/test_tools.py:375` assert it, and both are out of scope.
2026-10-30 19:55 hook post-run FAILED (exit 1):
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
> next: none ready
2026-10-30 20:03 omi-agent-engineer (claude):
> DONE
> - Files changed: `src/omi/project/tasks.py`, `src/omi/app/cli.py`, `src/omi/board/data.py`, `tests/test_omi.py`, `tests/test_board.py`, `tests/test_content.py`, `tests/test_cli.py`, `.omi/tasks/TASK-134.md`. Only the last three were touched this run; the rest are from the earlier run. Both test files are in scope, so the earlier NEEDS SCOPE no longer applies.
> - This run: the old `[review]` and `[planned]` label assertions now expect `[Đang làm]` and `[Chưa bắt đầu]`.
> - Commit: `feat(status): derive task phase, step position and review round from the workflow step`
> - Tests: `python3 tests/test_omi.py` ran end to end and exited 0, including `test_phase`. Skipped: `test_wheel_ships_web` (pip missing) and the browser layout and keyboard check (playwright missing).
> - Open issue: I kept the ` (step: X)` suffix on the first status line for in-progress tasks, because `tests/test_init.py:234` and `tests/test_tools.py:375` assert it and are outside scope.
2026-10-30 20:07 hook post-run passed:
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
| omi-agent-engineer | claude-sonnet-5-5 | medium | 26 | 8102 | 436265 | 581s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 14 | 1536 | 155193 | 500s | 1/1 omi-skill-lean-implementation | - |
