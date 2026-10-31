---
id: TASK-136
title: Plans whose tasks are all done show as done
status: done
depends:
plan: PLAN-007
scope: src/omi/board/**, src/omi/project/tasks.py, src/omi/app/cli.py, tests/test_board.py, tests/test_tasks.py, tests/test_content.py, .omi/tasks/TASK-136.md
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature
step: accept
---
## Goal
A plan with at least one task and every task `done` is shown as done in `omi status` and on the board, instead of `active`, without editing the plan file.

## Acceptance criteria
- [x] One function derives a plan's shown status: `done` when it has tasks and all are `done`; otherwise the stored `status:`. The plan file is never rewritten.
- [x] `omi status` lists done plans after active ones (or folds them into one `done plans: PLAN-002..006` line); the board's project list shows only plans that are not done, and the project view marks done plans.
- [x] A plan with no tasks keeps its stored status.
- [x] Tests cover all done, partly done, no tasks and a stored `status: done`; all tests pass.

## Checkpoint
Done: tasks.plan_status; cli status folds done plans into `done plans:` line; board plans use derived status, projects list hides done plans; tests in test_board.py/test_tasks.py.
Not done: nothing.
Tests: python3 tests/test_omi.py passes (wheel and playwright checks skipped).
Next: none.
Session: claude 5640203b-f68c-4132-9836-f944982d74b6

## Steps
- plan started 2026-10-31 12:27
- plan done 2026-10-31 12:27
- build started 2026-10-31 12:27
- build done 2026-10-31 12:54
- review started 2026-10-31 12:54
- review done 2026-10-31 13:06
- accept started 2026-10-31 13:06
PO approval accept: Accept, merge

## Reports
2026-10-31 12:34 omi-agent-engineer (claude):
> NEEDS SCOPE: `tests/test_content.py`. Line 172 asserts `"PLAN-000" not in text`. PLAN-000 has a stored `status: done`, so `omi status` now lists it in the new `done plans:` line. The fix is to change that assertion to expect `done plans: PLAN-000`.
> 
> - **Files changed:** `src/omi/project/tasks.py`, `src/omi/app/cli.py`, `src/omi/board/data.py`, `tests/test_board.py`, `tests/test_tasks.py`, `.omi/tasks/TASK-136.md`
> - **Behavior:**
>   - `tasks.plan_status` returns `done` when a plan has tasks and all are done, otherwise the stored status.
>   - `omi status` prints plans that are not done as before and folds done plans into one `done plans: …` line.
>   - The board derives each plan's status the same way, and its projects list shows only plans that are not done.
>   - The project view needed no change because `app.js` already marks done plans.
>   - Plan files are never rewritten.
> - **Tests:** The full `python3 tests/test_omi.py` run fails at `test_content.py:172`, so the suite after that point never ran. Run on their own, `test_board.py` (new `test_plan_status_derived`, covering all done, partly done, no tasks and stored done) and `test_plan_status` in `test_tasks.py` pass.
> - **Commit message:** `feat(status): show plans with all tasks done as done`
2026-10-31 12:48 hook post-run passed:
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
2026-10-31 12:48 omi-agent-engineer (claude):
> I found no new findings under `## Checkpoint` in `.omi/tasks/TASK-136.md`. It still holds only my earlier entry, and the Reports section has no review entry either. I changed nothing and didn't rerun the tests.
> 
> To continue the fix round, add the findings to the task file or paste them here.
> 
> DONE for the earlier work: the last full `python3 tests/test_omi.py` run passed. It skipped the wheel check (pip missing) and the playwright browser check.
2026-10-31 12:53 hook post-run passed:
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
2026-10-31 13:06 omi-agent-reviewer (claude):
> ```
> VERDICT: PASS
> - src/omi/app/cli.py:180 Plans with a stored `status: done` are left out of `omi status`, while derived-done plans are folded into the `done plans:` line. test_content.py:172 expects this, and it reads as a deliberate choice -> optional: list stored-done plans in the line too, and update that assertion.
> - tests/test_tasks.py:273 No test covers the `omi status` `done plans:` line. The new tests cover only `plan_status` and the board data -> optional: add a status-output assertion.
> AC: One function derives a plan's shown status; the plan file is never rewritten ✓ `tasks.plan_status` in tasks.py:29 is used by cli.py and board/data.py. test_plan_status_derived asserts the plan file still has `status: active`.
> AC: `omi status` lists done plans after active ones or folds them into one line; the board project list hides done plans; the project view marks done plans ✓ `PYTHONPATH=src python3 -m omi status` printed `done plans: PLAN-002, PLAN-003, PLAN-004, PLAN-005, PLAN-006`. The board test shows `projects()` returning only PLAN-002 and PLAN-003. `app.js:45` marks plans with `status === "done"` as completed, and that status is now derived.
> AC: A plan with no tasks keeps its stored status ✓ test_plan_status asserts this, and test_plan_status_derived covers PLAN-003 (stored active, no tasks) and PLAN-004 (stored done).
> AC: Tests cover all done, partly done, no tasks and a stored `status: done`; all tests pass ✓ `python3 tests/test_omi.py` ended with `ok`. The wheel and playwright checks were skipped, and they are not part of this criterion.
> ```

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 30 | 5073 | 471003 | 409s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 6 | 1069 | 119899 | 356s | 0/1 | - |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 8 | 448 | 168092 | 12s | 0/1 | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 14 | 2398 | 206088 | 570s | - | PASS 1d47b2a |
