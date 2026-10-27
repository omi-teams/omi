---
id: TASK-082
title: Model catalog for the Coordinator - concrete model and effort per tool, never codex-default/none
status: planned
depends: TASK-080, TASK-081
scope: src/omi/__init__.py, tests/**, src/omi/template/**, .omi/config.json, .omi/agents/**, AGENTS.md, .claude/skills/omi-task/SKILL.md
role: omi-agent-engineer
skills: [omi-skill-windows-powershell]
refs:
plan: PLAN-001
tool: codex
model: sonnet
effort: medium
workflow: omi-flow-feature
step:
---
## Goal
From the findings in `docs/research/models-claude.md` and `docs/research/models-codex.md`, give the Coordinator a catalog of concrete model + effort choices per tool, make every run use an explicit model and effort, and make every task-start question offer Claude Code and Codex. Covers gap #1 (empty `codex_models`).

## Acceptance criteria
- [ ] `.omi/config.json` (root and template) maps each alias for both tools to concrete IDs from the research (`models`, `codex_models`); the template no longer ships an empty `codex_models`.
- [ ] `python -m omi agents` writes a `## Models` section in `.omi/agents/CATALOG.md` (root and template): per tool, each model and effort with what it fits and what to avoid, generated from a `model_notes` block in `.omi/config.json` (one line each).
- [ ] No run goes out as `codex-default` or effort `none`: `omi run` resolves the alias to a concrete ID and an explicit effort for both tools, or stops with a message naming the missing `codex_models`/effort entry. Container name and Usage row always show the concrete model and effort. Tested.
- [ ] AGENTS.md (root and template) and `omi-task` SKILL.md (root and template): every task-start pick-list has two options, start with Claude Code (model/effort) and start with Codex (model/effort), one marked Recommended with its reason; the PO chooses.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:
