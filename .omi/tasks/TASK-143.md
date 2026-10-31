---
id: TASK-143
title: install-user also installs the omi guard edit hook
status: in-progress
depends:
plan: PLAN-007
scope: src/omi/setup/install.py, tests/test_install.py, .omi/tasks/TASK-143.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: opus
effort: high
step_settings:
workflow: omi-flow-feature-sensitive
step: build
---
## Goal
A detached repo keeps the Coordinator's edit guard: `omi install-user` adds the `PreToolUse` hook `python -m omi guard` (matcher `Edit|Write|MultiEdit|NotebookEdit`) to the user's Claude Code settings next to the SessionStart hook, so removing `.claude/settings.json` from a code repo (TASK-135) does not drop the guard.

## Acceptance criteria
- [x] `omi install-user` adds the guard hook once (idempotent on rerun, never duplicates an existing identical entry, keeps the user's other hooks and matchers) and records what it added the same way as the SessionStart hook.
- [x] `omi install-user --remove` removes only what install-user added (the guard entry, and the `PreToolUse` list only if install-user created it); the backup rule stays as today.
- [x] A settings file whose `hooks.PreToolUse` is not a list fails with the same `StateError` style as SessionStart, changing nothing.
- [x] Tests cover fresh install, rerun, existing user PreToolUse hooks kept, remove, and a malformed PreToolUse; all tests pass.

## Checkpoint
Coordinator note for review/security: the guard is now user-wide, so `omi guard` runs in every repo on the machine. Check scope.py:27-80 for non-omi repos: blocks any `.claude/settings*.json` edit outside a task branch (also ~/.claude/settings.json?), and a non-omi repo on a `task/*` branch reaches `state.resolve`. Say whether that is acceptable or must be limited to omi projects.
Done: Added tracked, idempotent PreToolUse guard installation/removal, validation, legacy manifest support, and acceptance tests.
Not done: No implementation work remains. Wheel packaging and browser layout/keyboard checks were skipped because pip and Playwright are unavailable.
Tests: python3 tests/test_install.py passed (all 11 test functions); python3 tests/test_omi.py exited 0 with ok. Both ran with PYTHONDONTWRITEBYTECODE=1 and TMPDIR=/work. Full suite skipped test_wheel_ships_web (pip missing) and test_browser_layout_and_keyboard (Playwright missing); Node DOM tests ran successfully. Earlier development runs failed before fixes, and the earlier full-suite run was interrupted and replaced by the successful final run.
Next: Coordinator reviews the scoped diff and commits; rerun the two optional checks in an environment with pip and Playwright. TASK-135 can proceed after review.
Session: codex 01a190a2-9685-7231-bbfd-99ed4f30a80e

## Steps
- plan started 2026-10-31 13:25
- plan done 2026-10-31 13:25
- architect started 2026-10-31 13:25
- architect skipped 2026-10-31 13:25: design given by the TASK-135 architect (T4): mirror the SessionStart hook handling
- build started 2026-10-31 13:25

## Reports
2026-10-31 13:43 omi-agent-engineer (codex):
> DONE
> Files changed: `src/omi/setup/install.py`, `tests/test_install.py`, `.omi/tasks/TASK-143.md`.
> Suggested commit: `fix(setup): install user-level edit guard hook`
> Tests: all 11 installer tests passed; full suite exited 0.
> Skipped: wheel packaging (pip missing), browser layout/keyboard checks (Playwright missing).
> Checkpoint updated. No implementation issues remain; no commit created.
2026-10-31 13:47 hook post-run passed:
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
| omi-agent-engineer | gpt-6-astra (codex) | high | 2749300 | 13822 | 2703872 | 1102s | 1/1 omi-skill-lean-implementation | - |
