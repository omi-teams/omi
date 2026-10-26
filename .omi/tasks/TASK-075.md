---
id: TASK-075
title: Install with pip --user from a tag; omi status warns on version and Dockerfile drift
status: in-progress
depends:
scope: README.md, src/omi/__init__.py, tests/**
role: omi-agent-engineer
skills: [omi-skill-windows-powershell]
refs:
plan:
tool:
model: sonnet
effort: low
workflow: omi-flow-feature
step:
---
## Goal
Hooks and AGENTS.md call `python -m omi`, which a pipx install cannot serve; one omi per machine is the accepted limit. Document the install that works, and make `omi status` say when a project and the installed omi disagree.

## Acceptance criteria
- [ ] README install/upgrade uses `python -m pip install --user "git+https://github.com/omi-teams/omi-squad2@v0.2.0"` (upgrade: same with the new tag, then `omi init` in each project); no pipx; one line says there is one omi per Python on the machine and how a developer of omi itself uses `pip install -e .` instead.
- [ ] `omi status`: when `.omi/version` is newer than the installed omi it prints one line `this project needs omi <stamp>; install it: python -m pip install --user "git+https://github.com/omi-teams/omi-squad2@v<stamp>"` (the existing older-stamp hint stays). Tested.
- [ ] `omi status`: when `docker/Dockerfile` exists and differs from the installed template's Dockerfile, it prints one line `docker/Dockerfile differs from the omi <version> template; review it (omi init never overwrites it)`; identical or absent prints nothing. Line endings (CRLF/LF) do not count as a difference. Tested.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:
