---
id: TASK-088
title: Bump omi to 0.3.0
status: planned
depends: TASK-087
plan: PLAN-001
scope: pyproject.toml, README.md, tests/test_omi.py, .omi/version, src/omi/template_shas.json
role: omi-agent-engineer
skills: []
refs: []
tool:
model: haiku
effort: low
workflow: omi-flow-feature
step:
---
## Goal
Release prep for 0.3.0 (PLAN-001 done criteria). Version is SemVer 0.x with `pyproject.toml` as the only source (decision 2026-10-26, TASK-074). Bump it so `omi --version` and the install instructions match the v0.3.0 tag the PO creates at promote.

## Acceptance criteria
- [ ] `pyproject.toml` version is `0.3.0`; `python -m omi --version` prints `omi 0.3.0`.
- [ ] README install line and `omi --version` example say `v0.3.0` / `omi 0.3.0`.
- [ ] This repo's `.omi/version` is `0.3.0`.
- [ ] `src/omi/template_shas.json` gains a `0.3.0` entry equal to the current template's hashes (`python -m omi template-shas src/omi/template 0.3.0`); the `0.2.0` entry is unchanged.
- [ ] Tests updated for the new version (only the version assertion; tag-parsing fixtures that use `v0.2.0` as sample data stay) and pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next: start with `omi-task TASK-088`. After merge: omi-release (rc), PO merges staging, then promote + tag v0.3.0.
