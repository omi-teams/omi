---
id: TASK-072
title: Coordinator picks model and effort per task in the task file
status: in-progress
depends: TASK-071
scope: src/omi/__init__.py, tests/**, src/omi/template/**, .omi/tasks/_template.md, AGENTS.md
role: omi-agent-engineer
skills: []
tool:
workflow: omi-flow-feature
step: build
---
## Goal
The Coordinator records its model choice in the task file (`model:` alias haiku|sonnet|opus or a full ID, `effort:`), so it survives resume and the quota switch; `omi run` resolves the alias for whichever tool runs. Order: `omi run --model/--effort` > task `model/effort` > role.

## Acceptance criteria
- [ ] `model:` and `effort:` in the task frontmatter override the role's; `--model/--effort` override both. Tested for claude and codex.
- [ ] An alias resolves through `models` for claude and `codex_models` for codex, also after a quota switch to the other tool; the container name and the Usage row show the resolved model, not the alias. Tested.
- [ ] A codex alias missing from `codex_models` still runs with `codex-default` and `omi run` prints one warning line naming the alias. Tested.
- [ ] `model` and `effort` are in `.omi/tasks/_template.md` (root and template) and are Coordinator-owned frontmatter (agents cannot change them).
- [ ] Template and root `AGENTS.md` say in one line that the Coordinator sets `model`/`effort` per task from the quota rules.
- [ ] A task's `tool:` (and `model`/`effort`) apply only to its write role (the implementer); read roles such as the reviewer keep their role's tool, so a codex-built task gets a claude review by default. `omi run --tool` still overrides. Tested.
- [ ] When an agent CLI exits non-zero for a reason other than a usage limit, `omi run` prints its error events (claude `result` is_error, codex `error`/`turn.failed`) and the exit code, and writes them to `## Reports`. Tested.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done: all criteria implemented + tested (Windows run not possible here).
Not done: Windows host test run.
Tests: python3 tests/test_omi.py ok (Linux).
Next: Coordinator review/commit.

## Steps
- plan started 2026-10-26 14:32
- plan done 2026-10-26 14:32
- build started 2026-10-26 14:32

## Reports
2026-10-26 14:34 omi-agent-engineer (claude):
> DONE (not run on the Windows host; the Linux tests pass).
> 
> - **Files changed:** `src/omi/__init__.py`, `tests/test_omi.py`, `.omi/tasks/_template.md`, `src/omi/template/dot-omi/tasks/_template.md`, `AGENTS.md`, `src/omi/template/AGENTS.md`, `.omi/tasks/TASK-072.md` (Checkpoint).
> - **Behaviour:**
>   - **Precedence:** a write role now takes `tool`, `model` and `effort` in the order `omi run` flags, then the task file, then the role. A read role keeps its own `tool` and ignores the task's `model`/`effort`.
>   - **Coordinator-owned:** `model` and `effort` are now Coordinator-owned frontmatter, so agent edits to them are reverted.
>   - **Codex alias:** a codex alias missing from `codex_models` runs with `codex-default` and prints one `WARNING` line naming the alias. This also covers the switch after a quota hit.
>   - **Failures:** when the CLI exits non-zero for a reason other than a usage limit, `omi run` prints its error events and `exit code N`, and writes both to `## Reports`.
> - **Docs:** one `AGENTS.md` line in each copy (root and template) says the Coordinator sets `model`/`effort` per task. `model:` and `effort:` are added to both task templates.
> - **Tests:** `python3 tests/test_omi.py` passes on Linux. New cases are in `test_tool_choice_and_quota_switch`.
> - **Commit message:** `feat(run): Coordinator sets model and effort per task; surface CLI errors`
> - **Open issue:** the Windows host test run is still needed.
2026-10-26 14:34 hook post-run passed:
> Conflict. The container name "/tmpwjc5grup-TASK-001-engineer-codex-gpt-x-medium-073410" is already in useBind for 0.0.0.0:8080 failed: port is already in usewrote /tmp/tmp8mmyb4c2/.omi/skills/CATALOG.md (2 skills)
> create AGENTS.md
> create docker/Dockerfile
> create docker/__pycache__/proxy.cpython-313.pyc
> create docker/prove.sh
> create docker/proxy.py
> create .claude/settings.json
> create .claude/skills/omi-idea/SKILL.md
> create .claude/skills/omi-release/SKILL.md
> create .claude/skills/omi-status/SKILL.md
> create .claude/skills/omi-task/SKILL.md
> create .omi/agents/CATALOG.md
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
> create .omi/plans/CATALOG.md
> create .omi/plans/PLAN-000.md
> create .omi/references/CATALOG.md
> create .omi/references/nextjs-app-router.md
> create .omi/references/postgres-conventions.md
> create .omi/rules/CATALOG.md
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
> [... truncated ...]
> ok

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 20 | 6884 | 324836 | 102s | 1/1 omi-skill-lean-implementation | - |
