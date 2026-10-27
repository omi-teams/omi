---
id: TASK-082
title: Model catalog for the Coordinator - concrete model and effort per tool, never codex-default/none
status: in-progress
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
step: build
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
Coordinator notes (2026-10-27):
- PO decision (.omi/decisions.md): codex_models haiku -> gpt-6-luna, sonnet -> gpt-6.1-sol, opus -> gpt-6-astra.
- Claude models: haiku -> claude-haiku-5-5, sonnet -> claude-sonnet-5-5, opus -> claude-opus-5-5. Do not map claude-fable-5-1: it answers "requires usage credits" on the PO login.
- "effort none" in the criteria means a missing effort label. Codex does accept `none` as a value, but omi must never send or show it by default.
- Efforts: Claude low|medium|high|xhigh|max; Codex none|low|medium|high|xhigh|max (+ultra on sol/astra/terra). Map omi efforts 1:1.
Done:
- Added approved concrete Claude/Codex alias mappings to root and template configs, with model_notes for each model and effort; regenerated both agent catalogs with ## Models.
- omi run requires concrete model IDs and explicit valid efforts; missing Codex mappings stop startup or quota fallback. Efforts map 1:1 (including max), and container names retain the concrete ID shown in Usage.
- Root/template AGENTS.md and omi-task guidance require both Claude Code and Codex task-start choices, concrete model/effort, exactly one Recommended option with a reason, and the PO's choice.
- Added regression tests for mappings, config-driven catalog generation, task-start guidance, missing/invalid settings, quota fallback, explicit effort levels, container names and Usage. Updated credential fixtures to pass concrete Codex IDs.
Not done:
- Windows host validation is unavailable in this Linux worker; Coordinator must run the same suite on the host.
Tests:
- PASS: python3 tests/test_omi.py (exit 0, final output: ok), Linux, 2026-10-27.
- PASS: PYTHONPATH=src python3 -m omi agents (exit 0; root catalog regenerated).
Next:
- Coordinator reviews the scoped diff, runs python3 tests/test_omi.py on Windows, then commits on the host. No worker commit.

## Steps
- plan started 2026-10-27 10:07
- plan done 2026-10-27 10:07
- build started 2026-10-27 10:07

## Reports
2026-10-27 10:14 omi-agent-engineer (codex):
> DONE
> Files: `src/omi/__init__.py`, `tests/test_omi.py`, root/template configs, agent catalogs, AGENTS.md, omi-task skills, and task checkpoint.
> Commit: `feat: add explicit per-tool model catalog and effort validation`
> Tests: `python3 tests/test_omi.py` PASS; catalog CLI PASS.
> Open issues: Windows host tests pending Coordinator validation. No commit made.
2026-10-27 10:15 hook post-run passed:
> Conflict. The container name "/tmpfvtu9hoz-TASK-001-engineer-codex-gpt-x-medium-031416" is already in useBind for 0.0.0.0:8080 failed: port is already in usecreate AGENTS.md
> create docker/Dockerfile
> create docker/prove.sh
> create docker/proxy.py
> create .claude/settings.json
> create .claude/skills/omi-idea/SKILL.md
> create .claude/skills/omi-release/SKILL.md
> create .claude/skills/omi-status/SKILL.md
> create .claude/skills/omi-task/SKILL.md
> create .claude/skills/omi-upgrade/SKILL.md
> create .omi/agents/omi-agent-architect.md
> create .omi/agents/omi-agent-designer-ui.md
> create .omi/agents/omi-agent-devops.md
> create .omi/agents/omi-agent-docs-writer.md
> create .omi/agents/omi-agent-engineer.md
> create .omi/agents/omi-agent-qa-tester.md
> create .omi/agents/omi-agent-researcher.md
> create .omi/agents/omi-agent-reviewer.md
> create .omi/agents/omi-agent-security-reviewer.md
> create .omi/config.json
> create .omi/decisions.md
> create .omi/hooks/post-run.sh
> create .omi/plans/PLAN-000.md
> create .omi/references/nextjs-app-router.md
> create .omi/references/postgres-conventions.md
> create .omi/rules/docker.md
> create .omi/rules/go.md
> create .omi/rules/nextjs.md
> create .omi/rules/postgres.md
> create .omi/rules/python.md
> create .omi/skills/.gitkeep
> create .omi/skills/data/omi-skill-data-review/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-docker-worker-pitfalls/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-incident/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-release-checklist/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-rollback/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-windows-powershell/SKILL.md
> create .omi/skills/qa-web/omi-skill-web-qa/SKILL.md
> create .omi/skills/quality/omi-skill-ci-workflow-audit/SKILL.md
> create .omi/skills/quality/omi-skill-debug-root-cause/SKILL.md
> create .omi/skills/quality/omi-skill-diff-security-review/SKILL.md
> create .omi/skills/quality/omi-skill-simplify-review/SKILL.md
> create .omi/skills/quality/omi-skill-verify-evidence/SKILL.md
> [... truncated ...]
> ok

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 2078722 | 12569 | 2007936 | 411s | 2/2 omi-skill-windows-powershell omi-skill-lean-implementation | - |
