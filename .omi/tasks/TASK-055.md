---
id: TASK-055
title: Pick Claude Code or Codex per role and task, switch on agent quota, resume after Coordinator quota
status: planned
depends: TASK-045, TASK-054
scope: src/omi/__init__.py, src/omi/template/**, .omi/agents/**, .omi/config.json, .omi/tasks/_template.md, .claude/skills/omi-task/**, AGENTS.md, tests/**, README.md
role: omi-agent-engineer
skills: [omi-skill-docker-worker-pitfalls, omi-skill-windows-powershell]
workflow: omi-flow-feature-sensitive
step:
---
## Goal
The Coordinator can run any role with Claude Code or Codex, chosen in files; an agent that runs out of quota is continued by the other tool automatically; a new Coordinator session (Claude Code or Codex) resumes a task with nothing lost.

## Acceptance criteria
- [ ] Role files accept `tool: claude|codex` (default claude) and task frontmatter accepts `tool:` (overrides the role); `omi run --tool` overrides both. The chosen tool is shown in the run output and the `## Usage` row.
- [ ] Codex gets its own model aliases in config (e.g. `codex_models`), so a role's `model:`/`effort:` resolve correctly for either tool; an unknown alias fails clearly before any container starts.
- [ ] When the agent's CLI stops on a usage/quota limit (patterns per tool, tested against recorded sample output), `omi run` always reruns the same role once with the other tool in the same worktree, with a prompt note that a partial diff exists; the switch is recorded in `## Usage` and `## Checkpoint`. If the other tool also hits its limit or has no token, it stops with exit code 5 and a `QUOTA:` line, nothing discarded.
- [ ] `omi run` appends the agent's final report (verdict/DONE line and summary) to the task file in the worktree, so a Coordinator that dies mid-run loses nothing.
- [ ] `omi status` shows, for an in-progress task, its current step and a `resume: omi-task <ID>` line; AGENTS.md and the omi-task skill say how to resume from Codex or Claude Code.
- [ ] The default Claude path (no `tool:` anywhere) is unchanged; `python tests/test_omi.py` passes.

## Checkpoint
Done:
Not done:
Tests:
Next:
