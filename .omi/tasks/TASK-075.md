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
step: build
---
## Goal
Hooks and AGENTS.md call `python -m omi`, which a pipx install cannot serve; one omi per machine is the accepted limit. Document the install that works, and make `omi status` say when a project and the installed omi disagree.

## Acceptance criteria
- [ ] README install/upgrade uses `python -m pip install --user "git+https://github.com/omi-teams/omi-squad2@v0.2.0"` (upgrade: same with the new tag, then `omi init` in each project); no pipx; one line says there is one omi per Python on the machine and how a developer of omi itself uses `pip install -e .` instead.
- [ ] `omi status`: when `.omi/version` is newer than the installed omi it prints one line `this project needs omi <stamp>; install it: python -m pip install --user "git+https://github.com/omi-teams/omi-squad2@v<stamp>"` (the existing older-stamp hint stays). Tested.
- [ ] `omi status`: when `docker/Dockerfile` exists and differs from the installed template's Dockerfile, it prints one line `docker/Dockerfile differs from the omi <version> template; review it (omi init never overwrites it)`; identical or absent prints nothing. Line endings (CRLF/LF) do not count as a difference. Tested.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done: README install, status version+Dockerfile hints, test_status_drift_hints
Not done: Windows run
Tests: new test and test_init_guard_status pass; full suite fails at test_workflows (CATALOG.md compare, not touched by this task, likely pre-existing)
Next: Coordinator checks test_workflows on host

## Steps
- plan started 2026-10-26 15:18
- plan done 2026-10-26 15:18
- build started 2026-10-26 15:18

## Reports
2026-10-26 15:19 omi-agent-engineer (claude):
> BLOCKED on the full suite: `python3 tests/test_omi.py` fails at `test_workflows`, which I did not touch. The new drift test and `test_init_guard_status` pass when run on their own.
> 
> - **Files changed:** `README.md`, `src/omi/__init__.py`, `tests/test_omi.py`, and the checkpoint in `.omi/tasks/TASK-075.md`.
> - **README:** the install and upgrade lines now use `python -m pip install --user "git+…@v0.2.0"`, with no pipx. One line says there is one omi per Python on the machine and that omi developers use `pip install -e .`.
> - **`omi status`:**
>   - A `.omi/version` stamp newer than the installed omi prints the "this project needs omi <stamp>; install it: …" line. The older-stamp hint is unchanged.
>   - A `docker/Dockerfile` that differs from the template's prints the "differs from the omi <version> template" line. CRLF and LF are treated as the same, and an identical or absent file prints nothing.
> - **Tests:** new `test_status_drift_hints`, registered in the runner. It covers the newer-stamp line, the CRLF-only case, a real Dockerfile difference, and an absent Dockerfile.
> - **Open issues:** the `test_workflows` failure is an assertion comparing the repo's `.omi/workflows/CATALOG.md` with the template's. I couldn't check whether it failed before my change, because `git` doesn't work in the worktree. The Windows run has not been done.
> - **Suggested commit:** `feat(status): warn on newer project stamp and Dockerfile drift; document pip --user install`
2026-10-26 15:19 hook post-run FAILED (exit 1):
> Conflict. The container name "/tmpqe7j5moa-TASK-001-engineer-codex-gpt-x-medium-081932" is already in useBind for 0.0.0.0:8080 failed: port is already in usewrote /tmp/tmpbk4w8aea/.omi/skills/CATALOG.md (2 skills)
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
> AssertionError
2026-10-26 15:21 hook post-run passed:
> Conflict. The container name "/tmpxtega9nn-TASK-001-engineer-codex-gpt-x-medium-082113" is already in useBind for 0.0.0.0:8080 failed: port is already in usewrote /tmp/tmpj6lio48d/.omi/skills/CATALOG.md (2 skills)
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
| omi-agent-engineer | claude-sonnet-5-5 | low | 18 | 3717 | 219869 | 51s | 2/2 omi-skill-windows-powershell omi-skill-lean-implementation | - |
