---
id: TASK-083
title: A task's own read role (e.g. the spike researcher) uses the task's tool, model and effort
status: in-progress
depends:
plan: PLAN-001
scope: src/omi/__init__.py, tests/test_omi.py, .omi/tasks/_template.md, src/omi/template/dot-omi/tasks/_template.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: sonnet
effort: medium
workflow: omi-flow-bugfix
step: review
---
## Goal
`omi run` applies a task's `tool/model/effort` only to write roles (`src/omi/__init__.py` around `write = am["access"] == "write"`). In a spike the task's own `role:` is the read-only researcher, so TASK-081 (`tool: codex`) ran on claude. Fix it at that one place: the task's settings also apply when the role being run is the task's own `role:`. Other read roles (reviewer, security-reviewer) keep their own settings so review stays independent.

## Acceptance criteria
- [ ] `omi run <role> <ID>` where `<role>` equals the task's `role:` uses the task's `tool`, `model` and `effort` (then the role's, then defaults), for read roles too; `--tool/--model/--effort` still win.
- [ ] Running a read role that is not the task's `role:` (e.g. `omi-agent-reviewer` on an engineer task) still ignores the task's tool/model/effort.
- [ ] A regression test in `tests/test_omi.py` fails before the fix and passes after, covering both cases.
- [ ] The `tool:`/`model:` comments in both `_template.md` copies say "write role or the task's own role" instead of "write role only".

## Checkpoint
Done: Applied task tool/model/effort to write roles or the task's own role; updated both templates and regression coverage.
Not done: None.
Tests: Regression failed before the code fix and passed after; python3 tests/test_omi.py passed (exit 0, ok).
Next: Coordinator reviews the diff and commits.

## Steps
- plan started 2026-10-27 09:48
- plan done 2026-10-27 09:49
- reproduce started 2026-10-27 09:49
- reproduce done 2026-10-27 09:53
- fix started 2026-10-27 09:53
- fix done 2026-10-27 09:53
- review started 2026-10-27 09:53

## Reports
2026-10-27 09:51 omi-agent-engineer (codex):
> DONE
> Files: `src/omi/__init__.py`, `tests/test_omi.py`, both scoped `_template.md` copies, `.omi/tasks/TASK-083.md`.
> Commit: `fix: apply task settings to its own read role`
> Tests: regression failed before fix, passed after; `python3 tests/test_omi.py` passed.
> Checkpoint updated. Open issues: none.
2026-10-27 09:53 hook post-run passed:
> Conflict. The container name "/tmpp7c57zxw-TASK-001-engineer-codex-gpt-x-medium-025157" is already in useBind for 0.0.0.0:8080 failed: port is already in usewrote /tmp/tmpy0ayje5t/.omi/skills/CATALOG.md (2 skills)
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
> create .omi/config.json
> create .omi/decisions.md
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
> [... truncated ...]
> ok
2026-10-27 09:56 omi-agent-reviewer (claude):
> VERDICT: PASS
> - `.omi/tasks/TASK-083.md` is outside the listed `scope`. The changes are only the checkpoint, steps and report, which is normal task bookkeeping. The post-run hook output pasted into Reports includes a Docker port-conflict message. It is harmless noise from the hook, not from this change.
> 
> AC: `omi run <role> <ID>` with `<role>` equal to the task's `role:` uses the task's tool, model and effort, and `--tool/--model/--effort` still win ✓. In `src/omi/__init__.py:2211-2237`, `task_settings = write or role == tm.get("role")` now gates the task's tool, effort and model. The explicit arguments are still first in each `or` chain, then the task's value, then the role's, then the default. The test sets `role: omi-agent-reviewer` on the task and asserts codex, `gpt-o` and `model_reasoning_effort=high`. It also asserts that explicit overrides win.
> AC: A read role that is not the task's `role:` still ignores the task's settings ✓. The test runs `omi-agent-reviewer` against a task with `tool: codex`, `model: opus` and `effort: high`. It asserts claude, `claude-sonnet-5-5` and medium.
> AC: The regression test fails before the fix and passes after, covering both cases ✓. `python3 tests/test_omi.py` passes and prints `ok`. I did not re-run it against the unfixed code. The own-role assertions rely on the new condition, so they would fail without it.
> AC: Both `_template.md` copies say "write role or the task's own role" ✓. The `tool:` and `model:` lines match in `.omi/tasks/_template.md` and `src/omi/template/dot-omi/tasks/_template.md`, and the test checks both files.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 748395 | 3580 | 712064 | 169s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 4 | 1136 | 41915 | 113s | - | PASS 3628654 |
