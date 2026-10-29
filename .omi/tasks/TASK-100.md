---
id: TASK-100
title: omi install-user: user-level skills, SessionStart hook, Codex AGENTS
status: in-progress
depends: TASK-097
plan: PLAN-004
scope: src/omi/install.py, src/omi/cli.py, tests/test_omi.py, README.md, src/omi/template/**
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature-sensitive
step: architect
---
## Goal
After one `omi install-user` per machine, opening Claude Code or Codex in an attached repo gives the Coordinator role and omi skills, with no file in the repo.

## Acceptance criteria
- [ ] `omi install-user` copies the omi skills to `~/.claude/skills/` and merges one SessionStart hook into `~/.claude/settings.json` (keeps every other key, idempotent, backup `settings.json.omi-bak` on first change). The hook prints the Coordinator rules plus `omi status` only when the cwd is an attached repo, else nothing. Tested on a temp HOME.
- [ ] Codex: the same rules go into `~/.codex/AGENTS.md` inside an `<!-- omi -->` block that is replaced on rerun, never duplicated, other content kept. Tested.
- [ ] `omi install-user --remove` takes out exactly what it added. Tested.
- [ ] `omi install-user` (and `--remove`) is listed in USAGE and pinned in `test_cli_characterization` (exit codes and key output).
- [ ] All tests pass on the Linux worker and the Windows host; in-repo mode behaviour is unchanged (existing tests untouched or only extended).

## Checkpoint
Done:
Not done:
Tests:
Next:

## Steps
- plan started 2026-10-29 10:33
- plan done 2026-10-29 10:33
- architect started 2026-10-29 10:33

## Reports
2026-10-29 10:36 omi-agent-architect (claude):
> RECOMMEND: B: put everything in a new `install.py` with a small manifest, and add a hidden `omi session-start` command that is the hook. It fits the layer rule, gives `--remove` exact undo data, needs no new template files (`omi init` copies everything under `template/`), and gives one source for the rules text.
> OPTIONS: A (all logic in `cli.py`, remove by pattern-matching what looks like omi's): smallest diff, but `cli.py` gets bloated, `--remove` can't tell a user's own `omi-*` skill or an empty `hooks` key from ours, and AC3 fails; B (`install.py` + manifest `~/.omi/install-user.json` recording skill sha256s, files and keys it created, and the hook command): exact undo and idempotent, costs one extra file in HOME; C (Codex block holds only a 3-line pointer "run `python -m omi session-start`, follow its output"): cheapest context in every Codex session, but AC2 says the same rules go in, so that needs a PO decision. Pick B.
> [... truncated ...]
> TASKS: one task, two engineer runs. Run 1: `install.py` + `install-user`/`--remove` covering skills, `settings.json`, Codex block and manifest, with tests for AC1–AC3 file effects, idempotency, backup, malformed input and exact removal. Run 2: `session-start` in `cli.py` (silent/attached/error cases), USAGE line, characterization pins, README. Both in the current scope; also widen scope to `.omi/rules/omi-modules.md` to add `install` to the layer order, as TASK-097 did.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 12 | 7452 | 209864 | 95s | - | n/a |
