---
id: TASK-098
title: omi attach: register a code repo in the omi-state repo
status: planned
depends: TASK-097
plan: PLAN-004
scope: src/omi/state.py, src/omi/upgrade.py, src/omi/cli.py, tests/test_omi.py, README.md
role: omi-agent-engineer
skills: []
refs: []
tool:
model:
effort:
step_settings:
workflow: omi-flow-feature
step:
---
## Goal
`omi attach [<repo path>]` turns any git repo into a detached omi project without touching it.

## Acceptance criteria
- [ ] `omi attach` in a code repo with an `origin` creates `projects/<name>/` in the state dir from the same template `omi init` uses (`.omi/`, `docker/`, hooks; no `AGENTS.md`/`.claude` there), writes `project.json`, commits it in the state repo, and never writes in the code repo. `<name>` defaults to the repo name; an existing one is refused unless it is the same URL. Tested.
- [ ] No state dir yet: `omi attach --state <git url>` clones it to `~/.omi/state` (or `OMI_STATE`); with no URL it `git init`s one and prints how to add a private remote. Tested with a local bare repo as remote.
- [ ] A second clone of the state repo (another `OMI_STATE`) resolves the same project for a fresh clone of the code repo in another dir. Tested.
- [ ] `omi attach` is listed in USAGE and pinned in `test_cli_characterization` (exit codes and key output).
- [ ] All tests pass on the Linux worker and the Windows host; in-repo mode behaviour is unchanged (existing tests untouched or only extended).

## Checkpoint
Done:
Not done:
Tests:
Next:
