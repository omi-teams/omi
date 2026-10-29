---
id: TASK-100
title: omi install-user: user-level skills, SessionStart hook, Codex AGENTS
status: in-progress
depends: TASK-097
plan: PLAN-004
scope: src/omi/install.py, src/omi/cli.py, tests/test_omi.py, README.md, src/omi/template/**, .omi/rules/omi-modules.md, .omi/rules/CATALOG.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature-sensitive
step: build
---
## Goal
After one `omi install-user` per machine, opening Claude Code or Codex in an attached repo gives the Coordinator role and omi skills, with no file in the repo.

## Acceptance criteria
- [ ] `omi install-user` copies the omi skills to `~/.claude/skills/` and merges one SessionStart hook into `~/.claude/settings.json` (keeps every other key, idempotent, backup `settings.json.omi-bak` on first change). The hook prints the Coordinator rules plus `omi status` only when the cwd is an attached repo, else nothing. Tested on a temp HOME.
- [ ] Codex: the same rules go into `~/.codex/AGENTS.md` inside an `<!-- omi -->` block that is replaced on rerun, never duplicated, other content kept. Tested.
- [ ] `omi install-user --remove` takes out exactly what it added. Tested.
- [ ] `omi install-user` (and `--remove`) is listed in USAGE and pinned in `test_cli_characterization` (exit codes and key output).
- [ ] All tests pass on the Linux worker and the Windows host; in-repo mode behaviour is unchanged (existing tests untouched or only extended).

## Checkpoint
Done: Implemented user skills installation, tracked reversible settings/AGENTS integration, SessionStart command, USAGE/README and acceptance tests.
Not done: Windows host execution (not available in Linux worker).
Tests: Six focused install/startup/CLI tests passed. Final-code python3 tests/test_omi.py passed on Linux (83 test functions, exit 0, ok); Windows host not run.
Next: Coordinator reviews the diff and runs python3 tests/test_omi.py on the Windows host before committing.

## Steps
- plan started 2026-10-29 10:33
- plan done 2026-10-29 10:33
- architect started 2026-10-29 10:33
- architect done 2026-10-29 10:36
- build started 2026-10-29 10:36

## Reports
2026-10-29 10:36 omi-agent-architect (claude):
> RECOMMEND: B: put everything in a new `install.py` with a small manifest, and add a hidden `omi session-start` command that is the hook. It fits the layer rule, gives `--remove` exact undo data, needs no new template files (`omi init` copies everything under `template/`), and gives one source for the rules text.
> OPTIONS: A (all logic in `cli.py`, remove by pattern-matching what looks like omi's): smallest diff, but `cli.py` gets bloated, `--remove` can't tell a user's own `omi-*` skill or an empty `hooks` key from ours, and AC3 fails; B (`install.py` + manifest `~/.omi/install-user.json` recording skill sha256s, files and keys it created, and the hook command): exact undo and idempotent, costs one extra file in HOME; C (Codex block holds only a 3-line pointer "run `python -m omi session-start`, follow its output"): cheapest context in every Codex session, but AC2 says the same rules go in, so that needs a PO decision. Pick B.
> [... truncated ...]
> TASKS: one task, two engineer runs. Run 1: `install.py` + `install-user`/`--remove` covering skills, `settings.json`, Codex block and manifest, with tests for AC1–AC3 file effects, idempotency, backup, malformed input and exact removal. Run 2: `session-start` in `cli.py` (silent/attached/error cases), USAGE line, characterization pins, README. Both in the current scope; also widen scope to `.omi/rules/omi-modules.md` to add `install` to the layer order, as TASK-097 did.
2026-10-29 10:43 omi-agent-engineer (codex):
> DONE — implemented `install-user`, reversible removal, and SessionStart integration.
> Files: `src/omi/install.py`, `src/omi/cli.py`, `tests/test_omi.py`, `README.md`.
> Also: `.omi/rules/omi-modules.md`, `.omi/rules/CATALOG.md`, task checkpoint.
> Suggested commit: `feat: add user-level omi Coordinator installation`
> Tests: `python3 tests/test_omi.py` passed on Linux, 83 test functions, exit 0.
> Open issue: Windows host tests not run; Coordinator validation pending. No commit created.
2026-10-29 10:47 hook post-run passed:
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
| omi-agent-architect | claude-opus-5-5 | high | 12 | 7452 | 209864 | 95s | - | n/a |
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 1683090 | 11845 | 1606912 | 415s | 1/1 omi-skill-lean-implementation | - |
