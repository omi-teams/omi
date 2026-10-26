---
id: TASK-071
title: Add omi hooks (pre-run, post-run, pre-merge) run in Docker
status: in-progress
depends: TASK-070
scope: src/omi/__init__.py, tests/**, src/omi/template/**, .omi/hooks/**, .claude/skills/omi-task/SKILL.md, AGENTS.md
role: omi-agent-engineer
skills: [omi-skill-docker-worker-pitfalls, omi-skill-windows-powershell]
tool:
workflow: omi-flow-feature-sensitive
step:
---
## Goal
Scripts `.omi/hooks/<event>.sh|.py` for events `pre-run`, `post-run`, `pre-merge` run in the Docker worker with the worktree as cwd; a non-zero exit blocks that step. Hooks are read from the main checkout, never from the worktree. Spec: `docs/specs/template-kinds.md` (Hooks).

## Acceptance criteria
- [ ] `omi run` runs `pre-run` before the agent and `post-run` after it; a non-zero exit stops the run (pre-run: agent not started; post-run: task not moved to review) and the hook output goes to `## Reports`. Tested.
- [ ] Hook files come from the main checkout; a hook added or changed inside the worktree is not run. Tested.
- [ ] Hooks run in the worker container with no host secrets or token env; no container is left behind. Tested where Docker is available, otherwise the docker command line is asserted.
- [ ] `python -m omi hook pre-merge <TASK-ID>` runs the hook against the task worktree and exits with its code; `omi-task` SKILL.md (root and template) calls it before merging.
- [ ] No hook file for an event means that step is a no-op.
- [ ] The template ships `post-run.sh` that runs the project's tests when it finds them (pytest, go test, npm test), otherwise exits 0; `omi init` creates it. Tested.
- [ ] Template and root `AGENTS.md` mention hooks in one line each.
- [ ] All tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
