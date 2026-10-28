---
id: TASK-097
title: Detached state root: .omi state outside the code repo
status: in-progress
depends: TASK-095, TASK-106
plan: PLAN-004
scope: src/omi/*.py, tests/test_omi.py, docs/specs/detached-mode.md, .omi/rules/omi-modules.md, .omi/rules/CATALOG.md, src/omi/template/dot-omi/hooks/post-run.sh
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: opus
effort: high
step_settings:
workflow: omi-flow-feature-sensitive
step: build
---
## Goal
Every omi command can read and write `.omi/`, `docker/` and hooks from a state dir that is not the code repo's git root, chosen by the code repo's remote URL; in-repo projects work as before.

## Acceptance criteria
- [x] A project is detached when `~/.omi/state/projects/<name>/project.json` names the code repo's `origin` URL (normalised: https/ssh, trailing `.git`); `OMI_STATE` overrides `~/.omi/state`. One function in a new `src/omi/state.py` resolves (state root, code root); every command uses it. Tested with temp dirs.
- [x] In a detached project, `status`, `step`, `plans`, `skills check`, `hook` and `run` read and write only the state dir; git branches, worktrees (`../<repo>.wt/<ID>`) and the scope check act on the code repo; the code repo's `git status` stays clean after a full `omi step` cycle. Tested with real git.
- [x] `omi run` gives the agent the task file and catalogs from the state dir inside the container (mounted read-only next to the worktree); the engineer never writes into the state dir. Tested.
- [ ] All tests pass on the Linux worker and the Windows host; in-repo mode behaviour is unchanged (existing tests untouched or only extended).

## Checkpoint
Done: Existing detached resolver, command routing, code-repo git/scope handling, and read-only /state worker mounts retained. Fixed the now-in-scope shipped post-run hook to read ${OMI_PROJECT_STATE:-.}/.omi/config.json while executing tests in the code worktree. Extended test_detached_default_hook_config to verify state configuration precedence, paths with spaces, code cwd, and unset/empty override fallback. Removed the obsolete scope blocker from the detached-mode spec.
Not done: Windows host and live Docker validation have not run; this worker provides Linux only and Docker execution is mocked by the suite. The cross-platform acceptance criterion remains unchecked pending Windows evidence.
Tests: Before the fix, the focused test_detached_default_hook_config executed and failed as expected (exit 0 instead of configured exit 7). After the fix, TMPDIR=/work PYTHONDONTWRITEBYTECODE=1 python3 tests/test_omi.py completed with exit 0 and final output ok on Linux/Python 3.13.5. All 70 test functions completed, including six detached tests, real-git fixtures, existing in-repo coverage, and mocked Docker argv checks. The shipped shell hook actually executed in the detached regression and in the existing test_version_stamp_package_hook/test_hooks tests. Windows host and live Docker execution were not performed.
Next: Coordinator reviews the diff and runs python3 tests/test_omi.py on Windows before closing the cross-platform acceptance criterion and committing on the host. No scope expansion is needed and no commit has been made.

## Steps
- plan started 2026-10-28 21:26
- plan done 2026-10-28 21:26
- architect started 2026-10-28 21:26
- architect done 2026-10-28 21:29
- build started 2026-10-28 21:29
- build done 2026-10-28 22:10
- review started 2026-10-28 22:10
- review failed 2026-10-28 22:10
- build started 2026-10-28 22:10

## Reports
2026-10-28 21:28 omi-agent-architect (claude):
> RECOMMEND: B. Add a `state.Project(state, code, detached)` resolver and pass it into every command entry point; only two task helpers branch on mode. Every function then says which root it uses, and in-repo mode keeps its current paths and commits exactly.
> OPTIONS: A, resolve state root and code root once in `cli` and replace `"."` with them: small diff, but the hidden mode differences stay scattered (where the live task file lives, whether scope is read via `git show development:`, `/work/` prompt paths, `commit_task_file`), so in-repo behaviour can drift. B, a `Project` value plus mode helpers: touches every command signature and needs a new module layer, but each mode difference lives in one place and can be tested. C, copy or symlink the state into the worktree and keep the code as it is: almost no code, but it breaks the clean `git status` criterion and the engineer could write into the state.
> STRUCTURE: New `state.py` (imports `core` only; layer it as `tools/creds/scope > state > core/github`):
> - `normalise_url(url)`: https, ssh and scp forms all become `host/owner/repo`, lowercase host, no `.git`.
> - `state_home()`: `OMI_STATE` or `~/.omi/state`, read at call time, never cached.
> - `resolve(cwd)`: code = `main_checkout` or toplevel; matches `projects/*/project.json` `{"remote": <normalised>}` (this format is the contract for TASK-098).
> - `task_file(p, tid)`: in-repo, the worktree copy else the main copy; detached, `state/.omi/tasks`.
> - `task_scope(p, wt, tid)`: in-repo, `git show development:`; detached, the state file.
> - `catalog_root(p, wt)`: in-repo `wt`; detached `p.state`.
> 
> [... truncated ...]
> - E2: `scope`/`hooks`/`docker`/`run` detached paths and the ro `/state` mount; real-git test of a full `omi step` cycle plus a run argv test asserting the code repo's `git status` stays clean. Scope: `src/omi/scope.py`, `hooks.py`, `docker.py`, `run.py`, `tools.py`, `tests/test_omi.py`, `docs/specs/detached-mode.md`.
2026-10-28 21:53 omi-agent-engineer (codex):
> NEEDS SCOPE: `src/omi/template/dot-omi/hooks/post-run.sh` — honor detached configuration via `OMI_PROJECT_STATE`.
> 
> - Changed: `src/omi/{state,cli,tasks,scope,hooks,run,docker,tools,upgrade}.py`; `tests/test_omi.py`.
> - Also changed: detached-mode spec, module rule/catalog, TASK-097 checkpoint.
> - Suggested commit: `feat(state): support detached project roots`
> - Tests: `python3 tests/test_omi.py` — 69 functions completed; new default-hook regression failed.
> - Open: hook template fix; Windows/live Docker unverified. No commit made.
2026-10-28 21:56 hook post-run FAILED (exit 1):
> OMI: outside.py is outside the scope of TASK-097. Stop and report NEEDS SCOPE to the Coordinator.
> OMI: projects/sample/.omi/tasks/TASK-097.md is outside the task worktree.
> OMI: .omi/tasks/TASK-097.md is outside the scope of TASK-097. Stop and report NEEDS SCOPE to the Coordinator.
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
> [... truncated ...]
> AssertionError: ('detached hook ignored state test command', 'post-run: no tests found, nothing to run\n', '')
2026-10-28 22:07 omi-agent-engineer (codex):
> DONE — detached hook configuration fixed; checkpoint updated.
> Changed: `src/omi/template/dot-omi/hooks/post-run.sh`, `tests/test_omi.py`, `docs/specs/detached-mode.md`, `.omi/tasks/TASK-097.md`.
> Suggested commit: `fix(hooks): honor detached project test configuration`
> Tests: `python3 tests/test_omi.py` — all 70 functions completed successfully on Linux.
> Open: Windows-host validation pending; Docker was mocked, not executed live.
> No commit made.
2026-10-28 22:09 hook post-run passed:
> OMI: outside.py is outside the scope of TASK-097. Stop and report NEEDS SCOPE to the Coordinator.
> OMI: projects/sample/.omi/tasks/TASK-097.md is outside the task worktree.
> OMI: .omi/tasks/TASK-097.md is outside the scope of TASK-097. Stop and report NEEDS SCOPE to the Coordinator.
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
> [... truncated ...]
> ok

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 18 | 6400 | 354949 | 77s | - | n/a |
| omi-agent-engineer | gpt-6-astra (codex) | high | 3219774 | 28128 | 3140608 | 1437s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-engineer | gpt-6-astra (codex) | high | 1498364 | 6368 | 1447680 | 615s | 1/1 omi-skill-lean-implementation | - |
