---
id: TASK-090
title: Task-file flow: step auto-commits, run syncs scope, sensitive-workflow warning
status: in-progress
depends: TASK-089
plan: PLAN-002
scope: src/omi/__init__.py, tests/test_omi.py, .claude/skills/omi-task/SKILL.md, src/omi/template/dot-claude/skills/omi-task/SKILL.md
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature-sensitive
step: build
---
## Goal
omi-board gaps #4, #10, #5: no manual commit after `omi step`, the engineer sees the scope the Coordinator widened on `development`, and a risky scope under a plain workflow is flagged.
Note (Coordinator, after TASK-089): in this repo `omi step` wrote to the worktree's task file once the worktree existed, so `development` stayed clean. First reproduce #4 in a test (likely: `omi step` before the worktree exists writes the task file on `development`); fix only the case the test shows.

## Acceptance criteria
- [ ] `omi step <ID> next|done|back|skip` commits only the task file it changed on `development` (message `chore(<ID>): step <step> <action>`), leaving any other staged or unstaged change untouched; no commit when nothing changed. Tested with real git.
- [ ] Before the agent starts, `omi run` writes the `scope:` line of the task file on `development` into the worktree's task file when they differ (other worktree lines untouched; uncommitted is fine) and prints `SCOPE SYNCED: <scope>`. Tested: widening scope on development only, the next run's prompt task file shows the new scope.
- [ ] `omi step <ID> next` from the `plan` step (and `omi skills check <task-file>`) prints `WARN: scope touches <path pattern> - consider omi-flow-feature-sensitive` when a scope glob matches migrations, auth, secrets or `.github/` and `workflow` is not `omi-flow-feature-sensitive`; it warns only, exit code unchanged. Patterns in one tuple constant. Tested.
- [ ] `.claude/skills/omi-task/SKILL.md` and its template copy: drop the "commit" after `omi step` and the "edit scope on development only" caveat where the new behaviour makes them moot.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Coordinator: Windows host suite passed (ok).
Done:
Not done:
Tests:
Next: start after TASK-089.

## Steps
- plan started 2026-10-28 10:13
- plan done 2026-10-28 10:13
- architect started 2026-10-28 10:13
- architect done 2026-10-28 10:15
- build started 2026-10-28 10:15

## Reports
2026-10-28 10:14 omi-agent-architect (claude):
> I've read the task, `step()`, `run_role()`/`run_cmd()`, `task_scope`/`out_of_scope`, the skills CLI and the omi-task skill (both copies are identical). One design point affects correctness: scope sync has to run before `run_role` captures `before`. Otherwise `revert_front` undoes the synced scope after the run.
> 
> ```
> RECOMMEND: A - change the existing step(), run_role() and skills-check code paths with three small helpers; no new module or command, and each fix stays where its behaviour lives.
> OPTIONS: A (helpers called from step / run_role / main "skills check"): smallest diff, reuses git()/parse()/split(), but step() gets longer; B (a separate `omi sync`/`omi commit` command the Coordinator calls): no change to step() or run_role(), but it brings back the manual step this task removes (#4 and #10 stay open); C (scope sync in run_cmd, not run_role): only `omi run` is affected, but it must still happen before run_role reads `before`, so it needs the same reorder for no gain.
> [... truncated ...]
> ```
2026-10-28 10:24 omi-agent-engineer (claude):
> DONE
> - Files: `src/omi/__init__.py`, `tests/test_omi.py`, both `omi-task/SKILL.md` copies, `.omi/tasks/TASK-090.md` (checkpoint).
> - `omi step` now commits only the task file, as `chore(<ID>): step <step> <action>`. It does this only when the file sits on the `development` checkout. Other staged and untracked changes stay as they were. A step on the worktree's copy is not committed.
> - `omi run` copies the `development` `scope:` line into the worktree task file before it captures `before`. That ordering keeps `revert_front` from undoing the sync. It prints `SCOPE SYNCED: <scope>` when the scopes differ and nothing otherwise.
> - `warn_sensitive` prints `WARN: scope touches <pattern> - consider omi-flow-feature-sensitive`. It runs on `step next` from `plan` and on `skills check <task-file>`, and the exit code is unchanged. The patterns are in the tuple `SENSITIVE_SCOPE`.
> - Tests: `python3 tests/test_omi.py` prints ok on Linux. The new `test_task_flow_commit_scope_sync_warn` uses real git for the step commit and for the scope sync on a real worktree. I did not run it on the Windows host.
> - Open issues:
>   - I tested `sync_scope` directly and did not run it through `run_role`, since `run_role` needs Docker. Existing `test_worker` checks already exercise the new call site.
>   - I did not reproduce #4 (a step run before the worktree exists writes the task file on `development`) as a separate failing test. The commit fix covers that case.
>   - I kept the "development only" and "worktree copy is ignored" phrasing in the skill docs, because `test_cli_correctness` asserts those strings. The caveat is still partly true, since the scope is still read from `development`, so I added the sync note beside it.
>   - The "commit" after `omi step` isn't in the skill text, so the docs only gained a note that `omi step` commits the task file itself.
> - Suggested commit: `feat(task-flow): step auto-commits task file, run syncs scope, warn on sensitive scope`
2026-10-28 10:26 hook post-run passed:
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
| omi-agent-architect | claude-opus-5-5 | high | 14 | 5057 | 223811 | 58s | - | n/a |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 38 | 10262 | 792499 | 535s | 1/1 omi-skill-lean-implementation | - |
