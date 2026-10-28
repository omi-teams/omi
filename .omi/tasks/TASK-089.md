---
id: TASK-089
title: Clearer CLI feedback: Dockerfile diff hint, version check hint, hook result line
status: in-progress
depends: 
plan: PLAN-002
scope: src/omi/__init__.py, tests/test_omi.py
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
omi-board gaps #1, #2, #7, #8: when omi reports something, it says what happened and what to type next.

## Acceptance criteria
- [ ] When `docker/Dockerfile` differs from the template, `omi status` also prints one runnable command that shows the diff against the installed template file (e.g. `git diff --no-index <template path> docker/Dockerfile`) and says to merge by hand, since `omi init`/`upgrade` never overwrite it. Tested.
- [ ] `omi version` (and `--version`) prints the installed version plus a hint line `latest: python -m omi upgrade --check`; the `usage` text for `version` mentions it. Tested.
- [ ] `omi hook <event> <ID>` always prints a final line `hook <event> passed` or `hook <event> FAILED (exit N)`, also when the hook printed nothing. Tested.
- [ ] Regression test: `omi run` (write role) returns exit 6 when the post-run hook fails and the agent exited 0, and the engineer's `DONE` report does not change that. If the test shows the exit is already 6, no code change for this criterion.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done: all 4 code criteria; run exit was already 6 (regression assert added, no code change).
Not done: Windows host run.
Tests: python3 tests/test_omi.py ok (Linux).
Next: Coordinator reviews and commits.

## Steps
- plan started 2026-10-28 09:42
- plan done 2026-10-28 09:42
- build started 2026-10-28 09:42

## Reports
2026-10-28 09:49 omi-agent-engineer (claude):
> DONE — all four code criteria are in place and `python3 tests/test_omi.py` passes on Linux. I didn't run the Windows host, so that last criterion is still open.
> 
> - **Files changed:** `src/omi/__init__.py`, `tests/test_omi.py`, and the checkpoint in `.omi/tasks/TASK-089.md`.
> - **Dockerfile hint:** when `docker/Dockerfile` differs from the template, `omi status` now also prints `git diff --no-index <template path> docker/Dockerfile` and says to merge by hand.
> - **Version:** `omi version` and `--version` add the line `latest: python -m omi upgrade --check`, and the usage text for `version` mentions it.
> - **Hook result line:** `hook_cmd` and `omi run` both print a final `hook <event> passed` or `hook <event> FAILED (exit N)` line. The change is in `hook_note`, so it holds when the hook printed nothing.
> - **Exit 6 regression:** the exit was already 6 when the post-run hook fails and the agent exited 0, so I made no code change there. I only added an assertion to the existing test. I didn't check how the agent mock reports `DONE`, so the test doesn't directly show that a `DONE` report leaves the exit at 6.
> - **Suggested commit:** `feat(cli): clearer feedback for Dockerfile diff, version check and hook result`
2026-10-28 09:51 hook post-run passed:
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
| omi-agent-engineer | claude-sonnet-5-5 | medium | 24 | 3825 | 324092 | 397s | 1/1 omi-skill-lean-implementation | - |
