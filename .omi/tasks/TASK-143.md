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
step:
---
## Goal
A detached repo keeps the Coordinator's edit guard: `omi install-user` adds the `PreToolUse` hook `python -m omi guard` (matcher `Edit|Write|MultiEdit|NotebookEdit`) to the user's Claude Code settings next to the SessionStart hook, so removing `.claude/settings.json` from a code repo (TASK-135) does not drop the guard.

## Acceptance criteria
- [ ] `omi install-user` adds the guard hook once (idempotent on rerun, never duplicates an existing identical entry, keeps the user's other hooks and matchers) and records what it added the same way as the SessionStart hook.
- [ ] `omi install-user --remove` removes only what install-user added (the guard entry, and the `PreToolUse` list only if install-user created it); the backup rule stays as today.
- [ ] A settings file whose `hooks.PreToolUse` is not a list fails with the same `StateError` style as SessionStart, changing nothing.
- [ ] Tests cover fresh install, rerun, existing user PreToolUse hooks kept, remove, and a malformed PreToolUse; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next: from the TASK-135 architect (T4): without it the omi repo loses the guard when `.claude/` is removed. TASK-135's removal PR waits for this task.
