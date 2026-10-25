---
id: TASK-008
title: Add omi-release skill for UAT candidate and promotion PRs
status: in-progress
depends: TASK-003
scope: src/omi/template/dot-claude/skills/omi-release/**, .claude/skills/omi-release/**, src/omi/template/AGENTS.md, AGENTS.md
---
## Goal
The squad prepares promotions (development → staging → main); the PO only tests and merges.

## Acceptance criteria
- [ ] The skill tags a candidate `rc-<date>-<sha7>` and opens a PR from development into staging with release notes, a test guide and a rollback plan.
- [ ] Only one candidate is open at a time; if a staging PR is already open, the skill reports it and stops.
- [ ] After the PO merges staging, the skill opens a PR from staging into main that points to the same candidate.
- [ ] The skill never merges into staging or main itself.

## Checkpoint
Done: skill + AGENTS lines. Not done: -
Tests: test_omi.py
Next: review
