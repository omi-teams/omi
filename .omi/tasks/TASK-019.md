---
id: TASK-019
title: Drop CLAUDE.md now that Claude Code loads AGENTS.md, and clean the cached worker image when idle
status: in-progress
depends: TASK-018
scope: src/omi/__init__.py, src/omi/template/**, .claude/skills/omi-task/**, .claude/agents/engineer.md, tests/**, README.md, AGENTS.md, CLAUDE.md
---
## Goal
Claude Code 2.1.302 loads AGENTS.md natively (Coordinator test 2026-10-25: a dir with only AGENTS.md, `claude -p` read its marker), so CLAUDE.md (`@AGENTS.md`) is redundant. The engineer in the container must not take the Coordinator's AGENTS.md as its own instructions. The PO rule: anything kept on purpose is removed once that purpose is gone.

## Acceptance criteria
- [ ] `omi init` no longer creates CLAUDE.md; the template file is removed; the root CLAUDE.md is removed; README's file table no longer lists it.
- [ ] The engineer run by `omi worker` does not follow the Coordinator's AGENTS.md. Find out whether `claude -p` in the container (with `--setting-sources user`) loads `/work/AGENTS.md`. If it does, stop it with a documented CLI flag or setting, or else make the engineer prompt state explicitly that AGENTS.md is for the Coordinator and must be ignored. Record what you found in the task checkpoint.
- [ ] `omi clean --all` also removes this repo's current worker image. The `omi-task` skill runs `omi clean --all` in its last step when `python -m omi status` shows no planned task left; otherwise it runs `omi clean` and keeps the image as cache for the next task. Template and root copies stay identical.
- [ ] Tests cover `omi init` without CLAUDE.md and `omi clean --all`; `python tests/test_omi.py` passes.

## Checkpoint
Done:
Not done:
Tests:
Next:
