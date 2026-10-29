---
id: TASK-118
title: Split tests/test_omi.py into test files by area
status: in-progress
depends: TASK-107
plan: PLAN-005
scope: tests/**
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-refactor
step: refactor
---
## Goal
The 5050-line `tests/test_omi.py` becomes several `tests/test_<area>.py` files (for example upgrade, install, attach/detached, init, github, worker, tasks, cli) with shared fakes in `tests/helpers.py`, so later tasks touch separate test files and can run in parallel. No product code changes.

## Acceptance criteria
- [ ] Each test file covers one area and stays under ~800 lines; shared fakes and fixtures (FakePopen, temp repos) live in `tests/helpers.py` and are imported, not copied.
- [ ] `python tests/test_omi.py` still runs every test and prints `ok` (CI and the post-run hook stay unchanged); each area file also runs on its own.
- [ ] The same 91 baseline tests exist before and after, by name; no test body changes beyond imports and helper references.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Baseline (Coordinator, development a426da4+): `python tests/test_omi.py` -> ok on the Windows host and in CI; 91 top-level `def test_` functions in tests/test_omi.py (`grep -c "^def test_" tests/test_omi.py`). Keep that set of names identical after the split.
Done: split into tests/helpers.py + 13 area files (attach, cli, content, creds, detached, github, hooks, init, install, tasks, tools, upgrade, worker), all <=614 lines; test_omi.py now imports and runs every area `main()` then prints ok. Same 91 `def test_` names (diff checked).
Not done: Windows host run.
Tests: Linux: python3 tests/test_omi.py -> ok; each tests/test_<area>.py exits 0 on its own.
Next: Coordinator verifies on the Windows host.

## Steps
- plan started 2026-10-29 14:54
- plan done 2026-10-29 14:54
- baseline started 2026-10-29 14:54
- baseline skipped 2026-10-29 14:54: baseline green: python tests/test_omi.py ok on host and CI after TASK-107 merge; test count recorded in Checkpoint
- refactor started 2026-10-29 14:54

## Reports
2026-10-29 15:05 omi-agent-engineer (claude):
> DONE. I split `tests/test_omi.py` into 13 area files plus a shared `tests/helpers.py`.
> 
> - **Files changed:** `tests/helpers.py` is new and holds the env setup, `FakePopen`, `git`, `no_egress`, `detached_project`, `detached_cli`, `state_remote` and `assert_download_cache_env`. The area files are `tests/test_{attach,cli,content,creds,detached,github,hooks,init,install,tasks,tools,upgrade,worker}.py`, each at most 614 lines. `tests/test_omi.py` is now a runner that imports every area file, runs each `main()` and prints `ok`. I also updated the checkpoint in `.omi/tasks/TASK-118.md`.
> - **Same tests:** the `def test_` names match the original 91, checked with `diff`. The bodies were moved by script with only imports changed.
> - **Test result (Linux):** `python3 tests/test_omi.py` printed `ok` and exited 0, and each of the 13 area files also exited 0 when run alone. Pytest was not run. My first full run overlapped with a second one and hit container-name and port 8080 conflicts. The conflicting run was my own duplicate. The runs that completed afterwards were clean.
> - **Open issues:** I didn't run it on the Windows host. The original file was 5128 lines, not 5050. The area files run in a different order from the old single `__main__` block, but nothing failed because of it.
> - **Suggested commit:** `refactor(tests): split test_omi.py into area test files with shared helpers`
2026-10-29 15:09 hook post-run passed:
> create AGENTS.md
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
> create .omi/skills/ui/omi-skill-ui-a11y-review/SKILL.md
> create .omi/skills/ui/omi-skill-ui-direction/SKILL.md
> create .omi/skills/ui/omi-skill-ui-direction/references/style-presets.md
> [... truncated ...]
> ok

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 30 | 9597 | 480506 | 673s | 1/1 omi-skill-lean-implementation | - |
