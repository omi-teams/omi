---
id: TASK-073
title: Codex agents in the worker do not load the project AGENTS.md
status: in-progress
depends:
scope: src/omi/__init__.py, tests/**
role: omi-agent-engineer
skills: []
refs:
plan:
tool:
model: haiku
effort: low
workflow: omi-flow-feature
step: build
---
## Goal
`AGENTS.md` at the repo root holds the Coordinator's instructions (talk to the PO in Vietnamese, never edit code). Codex reads it automatically from `/work`, so worker agents got Coordinator instructions on top of their role prompt (TASK-062/069: codex answered in Vietnamese). Make `codex_cmd` turn project docs off, e.g. `-c project_doc_max_bytes=0`, so a codex agent sees only its role prompt, like claude.

## Acceptance criteria
- [ ] `codex_cmd` passes the option that stops codex loading project docs (AGENTS.md); claude's command is unchanged. Tested on the argv.
- [ ] Real run (Coordinator, sandbox from `omi init` whose AGENTS.md says "Reply only in French"): `omi run --tool codex` engineer report is not in French and not in Vietnamese. Before the fix the same sandbox gives a French report.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Coordinator probe 2026-10-26 (sandbox from `omi init`, AGENTS.md "Reply only in French", codex gpt-6.1-sol): current code gives a French engineer report; with `-c project_doc_max_bytes=0` inserted right after `exec` in `codex_cmd`, the same run gives an English report. Use exactly that option.
Done: `codex_cmd` now emits `-c project_doc_max_bytes=0` right after `exec`; claude's command unchanged. Argv tests added/updated (codex with model, codex-default, claude negative); the two `exec -m` assertions in the run tests now expect the new prefix.
Not done: real run in Docker (acceptance 2) and the Windows host test run; not possible in this container, for the Coordinator.
Tests: `python3 tests/test_omi.py` rc=0 on Linux worker.
Next: Coordinator reviews the diff, runs the real codex probe and the Windows tests.

## Steps
- plan started 2026-10-26 14:47
- plan done 2026-10-26 14:47
- build started 2026-10-26 14:47

## Reports
2026-10-26 Coordinator real run: same French-AGENTS.md sandbox with this branch's code -> English codex report (before the fix: French). Windows host tests: ok.
2026-10-26 14:48 omi-agent-engineer (claude):
> DONE
> Files: `src/omi/__init__.py` (`codex_cmd` now emits `-c project_doc_max_bytes=0` right after `exec`; claude's command unchanged), `tests/test_omi.py` (codex argv assertions updated, plus codex-default and claude-negative checks), `.omi/tasks/TASK-073.md` (checkpoint).
> Commit: `fix(codex): stop codex loading project AGENTS.md in worker runs`
> Tests: `python3 tests/test_omi.py` rc=0 on the Linux worker.
> Open: the real `omi run --tool codex` check (acceptance 2) and the Windows test run aren't possible in this container; they're left for the Coordinator.
2026-10-26 14:48 hook post-run passed:
> Conflict. The container name "/tmp2_3_0yah-TASK-001-engineer-codex-gpt-x-medium-074813" is already in useBind for 0.0.0.0:8080 failed: port is already in usewrote /tmp/tmpylsaa7qa/.omi/skills/CATALOG.md (2 skills)
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
| omi-agent-engineer | claude-haiku-5-5 | low | 16 | 2687 | 185813 | 44s | 1/1 omi-skill-lean-implementation | - |
