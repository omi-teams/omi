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
step:
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
Done:
Not done:
Tests:
Next: start after TASK-089.
