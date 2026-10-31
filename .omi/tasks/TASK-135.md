---
id: TASK-135
title: Move the omi repo to detached mode on omi-state
status: in-progress
depends: TASK-137
plan: PLAN-007
scope: .omi/tasks/TASK-135.md, docs/**
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: sonnet
effort: medium
step_settings: architect=claude/opus/high
workflow: omi-flow-feature-sensitive
step: architect
---
## Goal
The omi repo's own plans, tasks and decisions live in `projects/omi/` on GitHub omi-teams/omi-state (`omi attach`), so they appear on the board like every other project; GitHub omi-state is the single source of omi state.

## Acceptance criteria
- [ ] `omi attach` registers this repo; `.omi/tasks`, `.omi/plans`, `.omi/decisions.md`, config, rules, skills and catalogs are copied to `projects/omi/` with history noted, committed and pushed to omi-state; `omi status` from the code repo gives the same output before and after.
- [ ] The in-repo omi state files are removed from the code repo in one PR (the `src/omi/template/**` copies stay); `omi status` prints no `WARN: in-repo omi files ignored` line.
- [ ] A fresh clone of omi-state shows project `omi` with PLAN-007 on the board.
- [ ] `docs/pilot-detached.md` (Vietnamese) records the migration commands and their output, and the rollback (restore the in-repo files from the commit before removal).

## Checkpoint
Done:
Not done:
Tests:
Architect (2026-10-31, option A): remove .omi/**, AGENTS.md, .claude/**, docker/** from the code repo; develop omi via `omi install-user`. Order: TASK-143 (install-user adds the guard hook) first; then T1 host/Coordinator: install-user, `omi status`>before, `omi attach`, copy .omi/{agents,config.json,decisions.md,hooks,plans,references,rules,skills,tasks,version,workflows} + docker/ over the seed, regenerate catalogs, commit `omi: import state from omi-teams/omi@<sha>; history: git log -- .omi AGENTS.md .claude` and push, `omi status`>after diff (only the WARN line may differ), fresh-clone check with OMI_STATE=<tmp> + board shows PLAN-007; freeze in-repo .omi edits from the copy until the removal PR merges. T2 engineer: removal PR; tests/test_cli.py:16, tests/test_content.py:137,252 read TEMPLATE only; tests/test_board.py:297 drops the omi-modules.md text check; `omi status` no WARN; tests pass. T3 docs/pilot-detached.md (Vietnamese): commands, outputs, rollback = `git checkout <pre-removal sha> -- .omi AGENTS.md .claude docker` + `git rm -r projects/omi` in omi-state.
Next: wait for TASK-143, then T1.

## Steps
- plan started 2026-10-31 13:19
- plan done 2026-10-31 13:19
- architect started 2026-10-31 13:19

## Reports
2026-10-31 13:24 omi-agent-architect (claude):
> I recommend option A: remove all of the in-repo omi state files, including `AGENTS.md`, `.claude/` and `docker/`. I haven't edited anything. The task's current scope (the task file and `docs/**`) is too narrow for this, so you need to widen it before the engineer runs.
> 
> ```
> RECOMMEND: A - remove .omi/, AGENTS.md, .claude/ and docker/ from the code repo; develop omi via `omi install-user` like any attached repo. Only this clears the WARN with no src change (attach.py:14 warns on all three of .omi/, AGENTS.md, .claude/) and matches the approved detached spec (no omi files in the code repo).
> OPTIONS: A: dogfoods detached mode, no src change, Codex workers stop seeing the Coordinator AGENTS.md (TASK-073) / loses the in-repo PreToolUse `omi guard` hook (install-user only adds SessionStart) and 3 tests read repo copies; B (keep AGENTS.md + .claude/, narrow warn_in_repo_files to .omi/): keeps guard / src change weakens the warn for every project, Coordinator rules loaded twice (session-start + AGENTS.md), against the spec; C (keep only .claude/settings.json for guard): still trips the WARN, fails AC2.
> STRUCTURE: Code repo keeps src/** (template copies included), tests/**, docs/**, README.md, project-overview.md, .github/, .gitattributes, .gitignore. Removed: .omi/**, AGENTS.md, .claude/**, docker/** (identical to src/omi/template/docker). State repo: ~/.omi/state/projects/omi/{project.json,.omi/*,docker/}. Tests that read repo copies switch to TEMPLATE only: tests/test_cli.py:16, tests/test_content.py:137,252; tests/test_board.py:297 drops the omi-modules.md text check (that rule becomes state).
> [... truncated ...]
> T4 is new work outside this task. I'd do it before the removal PR, because without it the Coordinator on the omi repo loses the edit guard, and this is a sensitive workflow.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 28 | 8948 | 526703 | 119s | - | n/a |
