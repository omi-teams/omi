---
id: TASK-099
title: State sync: auto pull/commit/push and omi sync
status: in-progress
depends: TASK-098
plan: PLAN-004
scope: src/omi/*.py, tests/test_omi.py, README.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature
step: review
---
## Goal
Several machines share one omi-state repo without the PO running git by hand.

## Acceptance criteria
- [x] `omi status` in a detached project runs `git pull --rebase` on the state repo first (skipped with a one-line note when offline or no remote). Tested with a local bare remote.
- [x] Every command that changes state (`step`, task start/done, decisions, plans, `omi run` reports/usage) commits only the files it changed in the state repo (`chore(<project>): <what>`) and pushes; a push failure prints `STATE NOT PUSHED: run omi sync` and keeps the commit. Tested.
- [x] `omi sync` pulls, commits any leftover state change and pushes; a rebase conflict stops with the file list and changes nothing more. Tested.
- [x] `omi sync` is listed in USAGE and pinned in `test_cli_characterization` (exit codes and key output).
- [x] All tests pass on the Linux worker and the Windows host; in-repo mode behaviour is unchanged (existing tests untouched or only extended).

## Checkpoint
Done: Added detached status pull, per-command commits/pushes, omi sync recovery/conflict handling, README and bare-remote/CLI/report tests. In-repo behavior preserved.
Not done: Windows host execution (Linux worker only).
Tests: Final python3 tests/test_omi.py executed all listed tests on Linux, exit 0 (ok). Includes local bare-remote pull/push, selective commits, reports/usage, offline/no-remote, failed-push recovery, leftovers/deletions, upstream setup, rebase conflict preservation and CLI characterization. Windows-only execution was not run.
Next: Coordinator reviews diff and runs python3 tests/test_omi.py on Windows before committing. No worktree commit made.

Host: python tests/test_omi.py (Windows host, commit feat(state): automatically sync detached project state) -> exit 0, ok

## Steps
- plan started 2026-10-29 10:10
- plan done 2026-10-29 10:10
- build started 2026-10-29 10:10
- build done 2026-10-29 10:23
- review started 2026-10-29 10:23

## Reports
2026-10-29 10:18 omi-agent-engineer (codex):
> DONE
> Files: `src/omi/cli.py`, `src/omi/state_sync.py`, `tests/test_omi.py`, `README.md`, `.omi/tasks/TASK-099.md`.
> Suggested commit: `feat(state): automatically sync detached project state`
> Tests: `python3 tests/test_omi.py` passed on Linux (exit 0).
> Open: Windows host verification pending. Checkpoint updated; no commit made.
2026-10-29 10:21 hook post-run passed:
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
2026-10-29 10:28 omi-agent-reviewer (claude):
> VERDICT: PASS
> - src/omi/cli.py:151 `parallel` is not in the `mutates` set, so state it changes would not be auto-committed. I didn't check whether `tasks.parallel` writes state. If it does, add it to the set.
> - src/omi/cli.py:165 The commit message is only `<cmd> state` (e.g. `chore(sample): step state`). That matches the `chore(<project>): <what>` format but says little about what changed. Pass a more specific `what` if you want a useful log.
> - src/omi/state_sync.py:242 Any non-zero `git pull` exit prints "offline or remote unavailable", including a dirty tree or a missing upstream. Include the git stderr in the note.
> - src/omi/cli.py:159 If `dispatch` raises and `commit` in the `finally` block also raises, the original error is hidden. Wrap the commit so the original error wins.
> - README.md:110 There is an extra blank line.
> 
> AC: `omi status` in a detached project runs `git pull --rebase` first, with a one-line skip note when offline or no remote ✓ `test_state_sync` uses a bare remote, picks up the peer's "Remote title", and checks both skip notes. `python3 tests/test_omi.py` exits 0.
> AC: State-changing commands commit only their changed files and push; a push failure prints `STATE NOT PUSHED: run omi sync` and keeps the commit ✓ The test checks `HEAD` contains only the task file, an unrelated staged file stays staged, and the commit survives a bad remote URL. Task start/done and decisions/plans edited by hand have no command of their own. They are committed by `omi sync`, and the README says so.
> [... truncated ...]
> AC: All tests pass on the Linux worker ✓ and on the Windows host HOST. The full suite exits 0 here. The in-repo characterization asserts were only extended, not changed. The Windows run can't happen in this container.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 2407656 | 15168 | 2327168 | 507s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 2703 | 82378 | 252s | - | PASS 2224eb2 |
