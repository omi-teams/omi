---
id: TASK-047
title: Record which skill files each role actually read
status: planned
depends: TASK-032
scope: src/omi/__init__.py, tests/**
role: omi-agent-engineer
skills: []
---
## Goal
Evidence that a role read its declared skills: `omi run` records the skill files the agent really opened, from its tool-call log, not from what the agent says.

## Acceptance criteria
- [ ] Claude runs use `--output-format stream-json --verbose` (Codex keeps `--json`); token usage and the final report are still parsed as today.
- [ ] From the tool-call events, collect the declared skill files (SKILL.md and declared references) that were opened by a Read tool call (or, for Codex, a command that reads the file).
- [ ] The `## Usage` row gets a `skills read` column: `n/m` plus the ids read; tasks without skills show `-`. Existing tables without the column still parse.
- [ ] When a declared skill was not read, `omi run` prints `SKILL NOT READ: <id>` after the report (warning, exit code unchanged).
- [ ] Tests: stream-json parsing (usage, report, read paths), Codex event parsing, the `n/m` cell, the warning; `python tests/test_omi.py` passes.

## Checkpoint
Done:
Not done:
Tests:
Next:
