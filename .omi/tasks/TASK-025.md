---
id: TASK-025
title: Skill group - delivery and operations
status: in-progress
depends: TASK-022
scope: .omi/skills/delivery-ops/**, .omi/skills/CATALOG.md, tests/test_omi.py, src/omi/template/dot-omi/skills/delivery-ops/**, .omi/decisions.md
---
## Goal
Skills for release, rollback, incidents and the Windows/Docker environment, from OMI's own experience and primary docs (not a summary repo).

## Acceptance criteria
- [ ] Skills: `release-checklist`, `rollback`, `incident`, `docker-worker-pitfalls`, `windows-powershell`.
- [ ] Each cites a concrete squad step or past problem (TASK-006, TASK-010, TASK-015, TASK-018) and the primary doc it is based on.
- [ ] Each passes `--check`, is at most 2000 tokens, and records source and license.
- [ ] Catalog regenerated; the template copy is identical.

## Checkpoint
Done: 5 skills in .omi/skills/delivery-ops (release-checklist, rollback, incident, docker-worker-pitfalls, windows-powershell), 534-706 tokens each; template copy identical; CATALOG regenerated.
Not done: nothing.
Tests: `omi skills --check` ok (15); python3 tests/test_omi.py ok.
Next: TASK-026

## Inputs
The container has no network, so base every skill on files in this repo: `.claude/skills/omi-release/SKILL.md`, `.claude/skills/omi-task/SKILL.md`, `.omi/tasks/TASK-006.md`, `TASK-010.md`, `TASK-015.md`, `TASK-018.md`, `.omi/decisions.md`, `docs/verification.md`, `docs/pilot.md`, `README.md`, `src/omi/template/docker/**`. Cite doc names only when the repo already links them; do not invent URLs or claims about Docker/PowerShell you cannot check in the repo. Frontmatter source: `source_repo` = https://github.com/omi-teams/omi-squad2, `source_ref` = a35ba0957a0a8e7e431fbbaba2b3df1f3588a79d, `source_file` = the repo files used, `source_license` = `internal (no LICENSE file yet)`, `source_use` = `rewrite`; if `--check` rejects this, report NEEDS SCOPE instead of changing the validator. Follow `.omi/skills/authoring/write-skill/SKILL.md`. Copy the new skills to `src/omi/template/dot-omi/skills/delivery-ops/` (identical), regenerate the catalog (`PYTHONPATH=src python3 -m omi skills`), run the whole `python3 tests/test_omi.py` before you report.

## Usage
| role | model | effort | input | output | cache | duration |
|---|---|---|---|---|---|---|
| engineer | claude-sonnet-5-5 | medium | 22 | 8653 | 396933 | 78s |
