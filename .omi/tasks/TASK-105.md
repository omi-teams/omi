---
id: TASK-105
title: CLI characterization test does not depend on what shares git's folder
status: in-progress
depends: TASK-104
plan: PLAN-003
scope: tests/test_omi.py
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-bugfix
step:
---
## Goal
CI on development is red since PR #100 (TASK-104), run 40663242734: `test_cli_characterization` (tests/test_omi.py:4004) sets PATH to git's folder and expects `tools: git ok, gh MISSING, docker MISSING` (line 4031). On the GitHub runner git lives in `/usr/bin`, next to gh and docker, so the line differs. The Linux worker and the Windows host keep git alone, which hid it. Test-only defect; src is fine.

## Acceptance criteria
- [ ] The test's PATH holds only git (and whatever git itself needs to run), independent of the machine: e.g. a temp folder with a link or shim to the real git, so gh, docker, claude and codex are always missing, also on ubuntu-latest where they share `/usr/bin`.
- [ ] No assertion in `test_cli_characterization` is removed or weakened; no src change.
- [ ] All tests pass on the Linux worker, on the Windows host, and in GitHub CI on the PR.

## Checkpoint
Done:
Not done:
Tests:
Next:
