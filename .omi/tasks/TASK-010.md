---
id: TASK-010
title: Polish omi github output and missing-gh error
status: planned
depends: TASK-003
scope: src/omi/__init__.py, tests/**
---
## Goal
Follow-ups from the TASK-003 review, plus tag protection for `omi-release` candidates.

## Acceptance criteria
- [ ] Re-running `omi github` prints `unchanged` for a ruleset whose live rules match the payload.
- [ ] `omi github` adds a tag ruleset on `rc-*` and `v*`: only the repository admin can update or delete tags (the old repo's lab showed the agent can move unprotected tags).
- [ ] If `gh` is not installed, every command that needs it prints a one-line message instead of a traceback.

## Checkpoint
Done:
Not done:
Tests:
Next:
