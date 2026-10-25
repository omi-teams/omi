---
id: TASK-010
title: Polish omi github output and missing-gh error
status: in-progress
depends: TASK-003
scope: src/omi/__init__.py, tests/**
---
## Goal
Follow-ups from the TASK-003 review, plus tag protection for `omi-release` candidates and two guard follow-ups from the TASK-012 review.

## Acceptance criteria
- [ ] Re-running `omi github` prints `unchanged` for a ruleset whose live rules match the payload.
- [ ] `omi github` adds a tag ruleset on `rc-*` and `v*`: only the repository admin can update or delete tags (the old repo's lab showed the agent can move unprotected tags).
- [ ] If `gh` is not installed, every command that needs it prints a one-line message instead of a traceback.
- [ ] Guard: the `.claude/settings*.json` check is case-insensitive (`.CLAUDE/Settings.json` on Windows is caught).
- [ ] Guard: writes to the main checkout's `.claude/settings*.json` are blocked for every caller, even when no task worktree exists.

## Checkpoint
Done: all 3 criteria (unchanged check via same(), omi-tags tag ruleset, gh-missing message in github()).
Not done: nothing. Coordinator applies `omi github` after merge.
Tests: python tests/test_omi.py ok
Next: review
