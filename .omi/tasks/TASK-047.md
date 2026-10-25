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
Round 1 fixes done: run_role test for SKILL NOT READ; old 7-column Usage header extended; read_commands limits Bash/Codex reads.
Review round 2 FAIL, fix both (edit only `## Checkpoint` in this file, never other sections):
1. `read_commands`: a segment that writes to the path is not a read: drop segments with `>`/`>>` redirects to it and `sed -i`. Negative tests.
2. Codex `cd dir && cat SKILL.md` or `cat ../x/SKILL.md` must count: match on `<skill dir name>/<file name>` or a bare `SKILL.md`/reference name after a `cd` into the skill dir (resolve against `cd` targets in the same command, or the event's `cwd` if present). Tests.
Tests: python3 tests/test_omi.py ok
Round 2 fixes done: read_commands strips redirects, skips sed -i, resolves cd/cwd; skills_read also matches <skill dir>/<file>. Negative + cd/cwd tests added; tests ok.
Review round 3 FAIL (PO: fix round 3 on opus/high), fix all, edit only `## Checkpoint` here:
1. Unwrap shells by basename: `/bin/bash -lc '...'`, `/usr/bin/env bash -c` etc. Test `/bin/bash -lc`.
2. In-place filter only for `sed` (`-\w*i\w*`, `--in-place*`); `grep -i`, `rg -i`, `less -i` stay reads. Catch `sed -ni`, `--in-place=.bak`. Tests.
3. `skills_read`: match file operands of read commands only, with a path boundary (whole operand equals or ends with `/<rel>`), not a substring of the command; `grep -c omi-skill-b/SKILL.md README.md` and `cat omi-skill-b/SKILL.md.bak` do not count. Tests.
Prefer one small tokenizer (`shlex.split`) over more regexes.
Next: review.

## Usage
| role | model | effort | input | output | cache | duration |
|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 22 | 5758 | 309528 | 65s |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 1933 | 71841 | 25s |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 20 | 6236 | 291198 | 60s |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 1911 | 64304 | 30s |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 14 | 4367 | 168226 | 55s |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 10 | 4062 | 133982 | 45s |
