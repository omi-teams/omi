---
id: TASK-100
title: omi install-user: user-level skills, SessionStart hook, Codex AGENTS
status: planned
depends: TASK-097
plan: PLAN-004
scope: src/omi/__init__.py, tests/test_omi.py, README.md, src/omi/template/**
role: omi-agent-engineer
skills: []
refs: []
tool:
model:
effort:
step_settings:
workflow: omi-flow-feature-sensitive
step:
---
## Goal
After one `omi install-user` per machine, opening Claude Code or Codex in an attached repo gives the Coordinator role and omi skills, with no file in the repo.

## Acceptance criteria
- [ ] `omi install-user` copies the omi skills to `~/.claude/skills/` and merges one SessionStart hook into `~/.claude/settings.json` (keeps every other key, idempotent, backup `settings.json.omi-bak` on first change). The hook prints the Coordinator rules plus `omi status` only when the cwd is an attached repo, else nothing. Tested on a temp HOME.
- [ ] Codex: the same rules go into `~/.codex/AGENTS.md` inside an `<!-- omi -->` block that is replaced on rerun, never duplicated, other content kept. Tested.
- [ ] `omi install-user --remove` takes out exactly what it added. Tested.
- [ ] All tests pass on the Linux worker and the Windows host; in-repo mode behaviour is unchanged (existing tests untouched or only extended).

## Checkpoint
Done:
Not done:
Tests:
Next:
