---
id: TASK-107
title: attach pushes state and prepares development
status: done
depends: 
plan: PLAN-005
scope: src/omi/upgrade.py, src/omi/state_sync.py, tests/test_omi.py, README.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature
step: accept
---
## Goal
Pilot gaps G2 and G3: after `omi attach` the state is on its remote and the code clone has a local `development` branch, with no manual step.

## Acceptance criteria
- [x] With a state remote, `omi attach` pushes its commit (sets upstream on an empty remote); a push failure keeps the commit and prints `STATE NOT PUSHED: run omi sync`.
- [x] If `origin/development` exists and no local `development` does, attach creates it tracking origin and prints one line; an existing local branch is untouched; the code repo gets no commit and no file.
- [x] Unit tests cover push success, push failure, empty remote, branch created and branch already present; all tests pass.

## Checkpoint
Host: python tests/test_omi.py (Windows host, worktree) -> ok, exit 0
Done: Attach reuses state push with upstream setup and failure recovery; prepares a missing development branch tracking origin without checkout or code files/commits; README updated; all acceptance behaviors covered by tests.
Not done: None.
Tests: python3 tests/test_omi.py passed (exit 0, final output ok); five focused attach tests also passed after final test cleanup. No acceptance tests skipped.
Next: Coordinator review and host commit; no worker commit made.

## Steps
PO approval accept: Chấp nhận, merge
- plan started 2026-10-29 14:15
- plan done 2026-10-29 14:15
- build started 2026-10-29 14:15
- build done 2026-10-29 14:24
- review started 2026-10-29 14:24
- review done 2026-10-29 14:34
- accept started 2026-10-29 14:34
- accept done 2026-10-29 14:34

## Reports
2026-10-29 14:20 omi-agent-engineer (codex):
> DONE
> Files changed: `src/omi/upgrade.py`, `tests/test_omi.py`, `README.md`, `.omi/tasks/TASK-107.md`.
> Suggested commit: `feat(attach): push state and prepare development branch`
> Tests: `python3 tests/test_omi.py` passed (exit 0); five focused attach tests passed; no acceptance tests skipped.
> Open issues: none. Checkpoint updated; no commit made.
2026-10-29 14:24 hook post-run passed:
> OMI: outside.py is outside the scope of TASK-097. Stop and report NEEDS SCOPE to the Coordinator.
> OMI: projects/sample/.omi/tasks/TASK-097.md is outside the task worktree.
> OMI: .omi/tasks/TASK-097.md is outside the scope of TASK-097. Stop and report NEEDS SCOPE to the Coordinator.
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
> [... truncated ...]
> ok
2026-10-29 14:33 omi-agent-reviewer (claude):
> VERDICT: PASS
> - tests/test_omi.py:4253 `test_attach_development_present` leaves the code repo's own `development` branch with no upstream, so the "untouched" check is weak in the other direction. The test does set `branch.development.merge`, which gives it coverage. No fix needed.
> - `.omi/tasks/TASK-107.md` is outside `scope` (task-file bookkeeping only). The post-run hook output pasted into its Reports section is noise and can be trimmed.
> 
> AC: With a state remote, `omi attach` pushes its commit (sets upstream on an empty remote); a push failure keeps the commit and prints `STATE NOT PUSHED: run omi sync` ✓ `attach` now calls `state_sync.push`, which uses `--set-upstream <remote> HEAD` when no upstream exists. `test_attach_push_success` and the updated `test_attach_clone_portability` check the remote head and upstream. `test_attach_push_failure` checks the message appears once, the commit is kept, and a later `omi sync` pushes it.
> AC: If `origin/development` exists and no local `development` does, attach creates it tracking origin and prints one line; an existing local branch is untouched; the code repo gets no commit and no file ✓ `prepare_development` runs `git branch --track`, so there is no checkout, commit or file. It runs on both the new-attach and "already attached" paths. `test_attach_development_created` checks the tracking upstream, HEAD, file contents and that the line prints once. `test_attach_development_present` checks the existing branch is unchanged.
> AC: Unit tests cover push success, push failure, empty remote, branch created and branch already present; all tests pass ✓ `python3 tests/test_omi.py` exited 0 and printed `ok`. The new tests are registered in `__main__`. Empty remote is covered by `test_attach_clone_portability` and the push-success test, where the state remote has no upstream yet.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 1149418 | 6176 | 1094912 | 297s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 10 | 1790 | 138282 | 481s | - | PASS 09763d7 |
