---
id: TASK-097
title: Detached state root: .omi state outside the code repo
status: in-progress
depends: TASK-095, TASK-106
plan: PLAN-004
scope: src/omi/*.py, tests/test_omi.py, docs/specs/detached-mode.md, .omi/rules/omi-modules.md, .omi/rules/CATALOG.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: opus
effort: high
step_settings:
workflow: omi-flow-feature-sensitive
step:
---
## Goal
Every omi command can read and write `.omi/`, `docker/` and hooks from a state dir that is not the code repo's git root, chosen by the code repo's remote URL; in-repo projects work as before.

## Acceptance criteria
- [ ] A project is detached when `~/.omi/state/projects/<name>/project.json` names the code repo's `origin` URL (normalised: https/ssh, trailing `.git`); `OMI_STATE` overrides `~/.omi/state`. One function in a new `src/omi/state.py` resolves (state root, code root); every command uses it. Tested with temp dirs.
- [ ] In a detached project, `status`, `step`, `plans`, `skills check`, `hook` and `run` read and write only the state dir; git branches, worktrees (`../<repo>.wt/<ID>`) and the scope check act on the code repo; the code repo's `git status` stays clean after a full `omi step` cycle. Tested with real git.
- [ ] `omi run` gives the agent the task file and catalogs from the state dir inside the container (mounted read-only next to the worktree); the engineer never writes into the state dir. Tested.
- [ ] All tests pass on the Linux worker and the Windows host; in-repo mode behaviour is unchanged (existing tests untouched or only extended).

## Checkpoint
Done:
Not done:
Tests:
Next:
