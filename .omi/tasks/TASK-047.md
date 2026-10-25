---
id: TASK-047
title: Record which skill files each role actually read
status: in-progress
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
Review round 1 fixes done: run_role test (SKILL NOT READ, rc 0, cell `1/2 omi-skill-a`); record_usage extends old 7-col header/separator; read_commands limits Codex/Claude Bash reads to cat/sed/head/tail/less/nl/rg/grep (negative tests for ls/rm/echo); Bash reads counted.
Not done: nothing.
Tests: python3 tests/test_omi.py ok
Next: review.

## Usage` row gets a `skills read` column: `n/m` plus the ids read; tasks without skills show `-`. Existing tables without the column still parse.
- [ ] When a declared skill was not read, `omi run` prints `SKILL NOT READ: <id>` after the report (warning, exit code unchanged).
- [ ] Tests: stream-json parsing (usage, report, read paths), Codex event parsing, the `n/m` cell, the warning; `python tests/test_omi.py` passes.
| omi-agent-engineer | claude-sonnet-5-5 | medium | 22 | 5758 | 309528 | 65s |

## Checkpoint
Review round 1 FAIL, fix all:
1. Add a `run_role` test (stub `subprocess.run` like "run_role records the harness numbers"): one skill read, one not; assert `SKILL NOT READ: <id>` printed, exit code unchanged, and the `skills read` cell in the task file.
2. `record_usage` on an existing 7-column `## Usage` table: extend its header and separator with `skills read` (old rows keep 7 cells, still parsed). Test it.
3. Codex (and Claude `Bash`) commands count as a read only for read commands (`cat`, `sed`, `head`, `tail`, `less`, `nl`, `rg`/`grep` with the file as argument); `ls`, `rm`, `echo` mentioning the path do not. Count Claude `Bash` reads too, so `cat SKILL.md` is not a false SKILL NOT READ. Add negative tests.
Done: stream-json cmd, opened_files/skills_read/skills_cell, skills read column (7- and 8-col tables parse), SKILL NOT READ warning, unit tests.
Not done: no end-to-end run_role test of the SKILL NOT READ print.
Tests: python3 tests/test_omi.py ok
Next: review.

## Usage
| role | model | effort | input | output | cache | duration |
|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 20 | 6236 | 291198 | 60s |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 1911 | 64304 | 30s |
