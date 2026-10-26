---
id: TASK-058
title: Fresh omi init project works out of the box (catalog, test command, gitignore)
status: in-progress
depends: TASK-057
scope: src/omi/__init__.py, src/omi/template/**, tests/**, README.md
role: omi-agent-engineer
skills: []
workflow: omi-flow-bugfix
step: reproduce
---
## Goal
The three defects found by the TASK-057 sandbox (docs/research/omi-eval.md): a fresh `omi init` project runs `omi run` with a workflow without manual fixes.

## Acceptance criteria
- [ ] `omi init` writes `.omi/skills/CATALOG.md` (and the agents/workflows catalogs) so a task with a workflow runs without `omi skills` first.
- [ ] The test command needs no pytest by default: `"test"` in config if set, else pytest only when it is importable, else each `tests/test_*.py` run as a script; the template config documents the `"test"` key.
- [ ] `omi init` adds a `.gitignore` with `__pycache__/` (never overwrites an existing one; appends the line if missing), so the agent's own test run is not reported OUT OF SCOPE.
- [ ] A test does a fresh `omi init` in a temp dir and checks all three; `python tests/test_omi.py` passes.

## Checkpoint
Done: init writes 3 catalogs + .gitignore; test_command falls back to script runner; config "test" key; test_init_fresh_project.
Not done: README untouched (nothing needed).
Tests: python3 tests/test_omi.py ok
Next: review

## Steps
- plan started 2026-10-26 10:34
- plan done 2026-10-26 10:34
- reproduce started 2026-10-26 10:34

## Reports
2026-10-26 10:35 omi-agent-engineer (claude):
> DONE
> - Files changed: `src/omi/__init__.py`, `src/omi/template/dot-omi/config.json`, `tests/test_omi.py`, `.omi/tasks/TASK-058.md`.
> - `omi init` now writes the skills, agents and workflows catalogs. It also adds `__pycache__/` to `.gitignore`: it creates the file if missing, appends the line if absent, and leaves everything else alone.
> - `test_command` order: config `"test"`, then `tests/test_omi.py` if present, then pytest if it is importable, else each `tests/test_*.py` run as a script (fails if any fails). I added `"test": ""` to the template config as the documentation for the key. JSON has no comments, so the empty value stands in as the doc.
> - New `test_init_fresh_project` covers the catalogs, the `.gitignore` handling, and the no-pytest fallback with pass and fail cases. `python3 tests/test_omi.py` passes.
> - Open: README untouched, because it didn't mention these. Re-running `omi init` regenerates the three catalogs, since they are generated files.
> - Suggested commit: `fix(init): write catalogs and .gitignore, run tests without pytest`

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 16 | 3379 | 181777 | 42s | 1/1 omi-skill-lean-implementation | - |
