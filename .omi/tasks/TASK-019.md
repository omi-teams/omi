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
Done: all 4 criteria. CLAUDE.md removed (root + template), README table updated, `omi clean --all` (removes current image), omi-task step 7 conditional clean, engineer.md (both copies) says to ignore /work/AGENTS.md.
Finding: could NOT verify live whether `claude -p --setting-sources user` loads /work/AGENTS.md (no OAuth token in this container: "Not logged in"). `--help` documents no flag that disables AGENTS.md/CLAUDE.md loading except --safe-mode/--bare-style options that also disable skills/agents/model-visible config, so used the prompt fallback (explicit ignore line in engineer prompt).
Tests: python tests/test_omi.py passes
Next: Coordinator may verify live with a token.
Live check (Coordinator, 2026-10-25, real token, haiku, worker image): `claude -p --setting-sources user` in the container with /work/AGENTS.md answered NONE (no project instructions loaded); the same run without `--setting-sources user` quoted `# OMI Squad` from /work/AGENTS.md. So `--setting-sources user` (already in engineer_cmd) is what keeps the Coordinator rules out; the engineer.md line is a second guard.
