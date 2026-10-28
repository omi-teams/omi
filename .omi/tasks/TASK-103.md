---
id: TASK-103
title: Windows test shell skips the WindowsApps WSL bash alias
status: in-progress
depends:
plan: PLAN-003
scope: src/omi/__init__.py, tests/test_omi.py
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature
step:
---
## Goal
On the PO's Windows host `test_command` picked `%LOCALAPPDATA%\Microsoft\WindowsApps\bash.exe`, a WSL app alias like System32's, and every `omi run` pre-check failed with `execvpe(/bin/bash) failed` (no WSL distro). Git Bash at `C:\Program Files\Git\bin\bash.exe` was installed but `Git\bin` is not on PATH (only `Git\cmd`). Found 2026-10-28 while starting TASK-094.

## Acceptance criteria
- [ ] On Windows, `test_command` never picks a WSL alias bash (System32 or WindowsApps); it finds Git Bash even when only `Git\cmd` is on PATH (e.g. `bash.exe` under the parent of `git.exe`'s directory, `bin\`), else falls back to `cmd`.
- [ ] A test covers the WindowsApps skip and the Git Bash lookup without needing Windows.
- [ ] All tests pass on the Linux worker and on the Windows host with the PATH as it is (no `Git\bin` added).

## Checkpoint
Done:
Not done:
Tests:
Next:
