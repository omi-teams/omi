---
id: TASK-078
title: Role prompts and init defaults - scope is write-only, batched NEEDS SCOPE, LF, quiet telemetry, allowlist by stack
status: in-progress
depends: TASK-077
scope: .omi/agents/**, .omi/skills/**, src/omi/template/**, src/omi/__init__.py, tests/**, docker/**, .claude/skills/omi-idea/SKILL.md
role: omi-agent-engineer
skills: []
refs:
plan: PLAN-001
tool: claude
model: sonnet
effort: medium
workflow: omi-flow-feature
step: build
---
## Goal
Gaps #2 #12 #13 #16 #19 #20 (omi-board session 97bfceb1).

## Acceptance criteria
- [ ] #16 #20 `omi-agent-engineer.md` (root and template) says: read any file you need; `scope` limits only what you write; when you need more scope, list every extra path at once in one `NEEDS SCOPE` report, and check which existing tests your change affects. `omi-skill-task-brief` (root and template) reminds the Coordinator to put affected tests in scope.
- [ ] #12 When the tool is codex, `omi run` appends one line to the prompt about known codex worker limits (deleting files with `rm` may be refused: use `git rm` or `python3 -c "import os; os.remove(...)"`). Tested on the codex argv.
- [ ] #19 `omi init` creates `.gitattributes` with `* text=auto eol=lf` when missing (never overwrites). Tested.
- [ ] #13 The proxy (template `docker/proxy.py` and this repo's `docker/proxy.py`) still blocks known codex/claude telemetry hosts (`ab.chatgpt.com`, `*.oaiusercontent.com`, `statsig.anthropic.com`, `sentry.io`) but does not print BLOCKED lines for them. Tested.
- [ ] #2 `.claude/skills/omi-idea/SKILL.md` (root and template) has a stack -> `network_allow` table (npm: registry.npmjs.org; Go: proxy.golang.org, sum.golang.org, storage.googleapis.com; Python: pypi.org, files.pythonhosted.org) and says to propose it to the PO when the stack is chosen.
- [ ] Skill and agent catalogs regenerated; `python -m omi skills --check` passes; all tests pass on the Linux worker and the Windows host.

## Checkpoint
Done: all criteria (agent/brief prompts, codex limits line, .gitattributes, quiet proxy hosts, omi-idea table), catalogs regenerated.
Not done: Windows host run (not available here).
Tests: python3 tests/test_omi.py ok; skills --check ok.
Next: Coordinator review.

## Steps
- plan started 2026-10-26 22:00
- plan done 2026-10-26 22:00
- build started 2026-10-26 22:00

## Reports
2026-10-26 22:02 omi-agent-engineer (claude):
> DONE. I couldn't run the tests on the Windows host from here.
> 
> - **Changed:**
>   - Prompts and skills (root and template copies): `omi-agent-engineer.md`, `omi-skill-task-brief/SKILL.md` and `.claude/skills/omi-idea/SKILL.md`.
>   - Code: `src/omi/__init__.py` (codex limits line, `.gitattributes` in `init`), `docker/proxy.py` and `src/omi/template/docker/proxy.py`.
>   - Other: `tests/test_omi.py`, `.omi/agents/CATALOG.md`, `.omi/skills/CATALOG.md`, `TASK-078.md`.
> - **What each change does:**
>   - `scope` now limits only writes, and the engineer lists all extra paths in one `NEEDS SCOPE` report.
>   - The task-brief skill reminds the Coordinator to put affected tests in scope.
>   - `codex_cmd` appends one line about the `rm` limit (use `git rm` or `os.remove`).
>   - `omi init` creates `.gitattributes` with `* text=auto eol=lf` and never overwrites it.
>   - The proxy still blocks the four telemetry hosts but no longer prints BLOCKED for them.
>   - The omi-idea skill has the stack → `network_allow` table and says to propose it to the PO when the stack is chosen.
> - **Tests:** `python3 tests/test_omi.py` prints `ok`, and `omi skills --check` passes (19 skills). I added tests for the codex argv, `.gitattributes`, and quiet proxy hosts. I ran the module with `PYTHONPATH=src` because `python -m omi` isn't importable from `/work` here.
> - **Open issue:** `src/omi/template/dot-omi/agents/CATALOG.md` already differed from the root one before my changes (the security-reviewer summary text). I left it alone.
> - **Suggested commit:** `feat(omi): write-only scope, batched NEEDS SCOPE, LF default, quiet telemetry, stack allowlist`
2026-10-26 22:03 hook post-run passed:
> Conflict. The container name "/tmph6g03nz4-TASK-001-engineer-codex-gpt-x-medium-150250" is already in useBind for 0.0.0.0:8080 failed: port is already in usewrote /tmp/tmpvrs749yk/.omi/skills/CATALOG.md (2 skills)
> create AGENTS.md
> create docker/Dockerfile
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
| omi-agent-engineer | claude-sonnet-5-5 | medium | 22 | 5132 | 322092 | 117s | 1/1 omi-skill-lean-implementation | - |
