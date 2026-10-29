---
id: TASK-109
title: omi step approve, reopen after CI failure, task ID in PR titles
status: in-progress
depends: TASK-118
plan: PLAN-005
scope: src/omi/tasks.py, src/omi/template/dot-claude/skills/omi-task/SKILL.md, .claude/skills/omi-task/SKILL.md, tests/test_tasks.py, .omi/tasks/TASK-109.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature
step: build
---
## Goal
Pilot gaps G5, G6 and G9 (found in TASK-107: CI fails after accept and `omi step back` cannot reopen a completed workflow): a PO approval is recorded by a command in the right place, and every squash commit names its task.

## Acceptance criteria
- [ ] `omi step <ID> approve --why "<PO words>"` writes `PO approval <current step>: <words>` under `## Steps` of the authoritative task file (state in detached mode), refuses when the current step is not a `po` gate, and commits like other step changes.
- [ ] `omi step <ID> reopen --why "<reason>"` on a completed workflow restarts its last write step, logs the reason under `## Steps`, and makes the po gate need a fresh approval line; refused while a step is running.
- [ ] The omi-task skill (template and repo copy) uses `omi step <ID> approve` and creates PRs with `--title "<type>: <title> (<ID>)"` instead of `--fill`, and on red CI after accept uses `omi step <ID> reopen`.
- [ ] Both actions reuse the existing `--why` argument so `src/omi/cli.py` is untouched (its usage line is updated in TASK-110); README is left to TASK-110.
- [ ] Tests in tests/test_tasks.py cover approve in in-repo and detached mode and the refusal; all tests pass.

## Checkpoint
Done: Review round 1 fix completed: added --body "<one-paragraph summary of the change>" to gh pr create in both scoped omi-task skill copies, keeping them identical. Extended the existing skill command assertion to require the body argument. No other implementation changes in this round.
Not done: Coordinator review and host commit are pending; no commit created in the worker.
Tests: python3 tests/test_tasks.py passed (all 7 test functions in main, exit 0); python3 tests/test_omi.py passed (ok, exit 0). No test skips reported; fixture messages about skipping existing files are installer behavior.
Next: Coordinator reviews the fix and commits; suggested message: fix(tasks): supply PR body in task skill.

## Steps
- plan started 2026-10-29 16:07
- plan done 2026-10-29 16:07
- build started 2026-10-29 16:07
- build done 2026-10-29 16:21
- review started 2026-10-29 16:21
- review failed 2026-10-29 16:27
- build started 2026-10-29 16:27

## Reports
2026-10-29 16:16 omi-agent-engineer (codex):
> DONE
> Files: `src/omi/tasks.py`, `tests/test_tasks.py`, both scoped `omi-task/SKILL.md` copies, `.omi/tasks/TASK-109.md`.
> Suggested commit: `feat(tasks): add PO approval and reopen completed workflows`
> Tests: `python3 tests/test_tasks.py` and `python3 tests/test_omi.py` passed; no skips reported.
> Checkpoint updated. Open issues: none. No commit created.
2026-10-29 16:20 hook post-run passed:
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
2026-10-29 16:27 omi-agent-reviewer (codex):
> VERDICT: FAIL
> - .claude/skills/omi-task/SKILL.md:24 (also template copy) Removing `--fill` leaves PR creation without a body, prompting for input and blocking unattended execution ([CLI documentation](https://cli.github.com/manual/gh_pr_create)) -> Add `--body-file` to both commands.
> AC: approve records words in authoritative state, refuses non-PO gates, and commits like other changes ✓ Routing, refusal, CLI parsing, and commit-routing tests passed.
> AC: reopen restarts the last write step, logs the reason, requires fresh approval, and refuses running steps ✓ Tests passed; approval invalidation also checked against five existing task logs.
> AC: both skill copies use approve, task-bearing PR titles, and reopen after red CI ✗ Required text is present, but PR creation needs the body fix above.
> AC: reuse --why; leave cli.py and README untouched ✓ Existing parser exercised; neither file appears in the diff.
> AC: approval tests cover in-repo/detached modes and refusal; all tests pass ✓ Task tests passed; `python3 tests/test_omi.py` exited 0 with `ok`.
2026-10-29 16:31 omi-agent-engineer (codex):
> DONE
> Files changed: both scoped omi-task/SKILL.md copies, tests/test_tasks.py, .omi/tasks/TASK-109.md.
> Added PR body argument and regression assertion; checkpoint updated.
> Suggested commit: `fix(tasks): supply PR body in task skill`
> Tests: `python3 tests/test_tasks.py` and `python3 tests/test_omi.py` passed; no test skips reported.
> Open issues: none. No commit created.
2026-10-29 16:34 hook post-run passed:
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
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 1821973 | 11921 | 1762304 | 565s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | gpt-6.1-sol (codex) | medium | 1306369 | 3432 | 1240192 | 258s | - | FAIL 37100f6 |
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 760625 | 1813 | 696320 | 227s | 1/1 omi-skill-lean-implementation | - |
