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
step: security
---
## Goal
After one `omi install-user` per machine, opening Claude Code or Codex in an attached repo gives the Coordinator role and omi skills, with no file in the repo.

## Acceptance criteria
- [x] `omi install-user` copies the omi skills to `~/.claude/skills/` and merges one SessionStart hook into `~/.claude/settings.json` (keeps every other key, idempotent, backup `settings.json.omi-bak` on first change). The hook prints the Coordinator rules plus `omi status` only when the cwd is an attached repo, else nothing. Tested on a temp HOME.
- [x] Codex: the same rules go into `~/.codex/AGENTS.md` inside an `<!-- omi -->` block that is replaced on rerun, never duplicated, other content kept. Tested.
- [x] `omi install-user --remove` takes out exactly what it added. Tested.
- [x] `omi install-user` (and `--remove`) is listed in USAGE and pinned in `test_cli_characterization` (exit codes and key output).
- [x] All tests pass on the Linux worker and the Windows host; in-repo mode behaviour is unchanged (existing tests untouched or only extended).

## Checkpoint
Done: Implemented user skills installation, tracked reversible settings/AGENTS integration, SessionStart command, USAGE/README and acceptance tests.
Not done: Windows host execution (not available in Linux worker).
Tests: Six focused install/startup/CLI tests passed. Final-code python3 tests/test_omi.py passed on Linux (83 test functions, exit 0, ok); Windows host not run.
Next: Coordinator reviews the diff and runs python3 tests/test_omi.py on the Windows host before committing.

Host: python tests/test_omi.py (Windows host, commit feat: add user-level omi Coordinator installation) -> exit 0, ok

## Steps
- plan started 2026-10-29 10:33
- plan done 2026-10-29 10:33
- architect started 2026-10-29 10:33
- architect done 2026-10-29 10:36
- build started 2026-10-29 10:36
- build done 2026-10-29 10:49
- review started 2026-10-29 10:49
- review done 2026-10-29 10:54
- security started 2026-10-29 10:54

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
2026-10-29 10:54 omi-agent-reviewer (claude):
> VERDICT: PASS
> - src/omi/install.py:202 The hook command is the bare `python -m omi session-start`. It silently fails (or prints an error at session start) on machines where `python` is absent, as on many Linux/macOS setups, or where omi isn't importable by that interpreter. This matches the repo's `python -m omi` convention, so I'm not failing it. -> Optionally record `sys.executable` in the hook command at install time.
> - src/omi/install.py:249 `install_user` is about 110 lines of dense branching (manifest validation, remove and install in one function). It works and is tested, but it is hard to maintain. -> Split it into validate, remove and install helpers.
> 
> AC: `install-user` copies skills to `~/.claude/skills/` and merges one SessionStart hook (keeps other keys, idempotent, `.omi-bak` backup on first change). The hook prints rules plus status only in an attached repo. ✓ `test_install_user` and `test_install_user_existing_integration` run on a temp HOME. They cover other-key preservation, an idempotent snapshot rerun, and backup bytes equal to the original. `test_user_session_start` covers the attached and non-attached cases. A manual run in a non-repo cwd printed nothing and exited 0.
> AC: Codex rules go in `~/.codex/AGENTS.md` inside an `<!-- omi -->` block that is replaced on rerun, never duplicated, other content kept. ✓ `test_install_user` checks one block and keeps the user's text. `test_install_user_existing_integration` checks that the block is replaced in place. `test_install_user_invalid_input` checks malformed blocks.
> [... truncated ...]
> AC: All tests pass on the Linux worker and the Windows host; in-repo mode is unchanged. ✓ for Linux: `python3 tests/test_omi.py` exited 0 and printed ok. HOST for Windows: the Windows host run is not possible in this container. Existing tests were only extended.
2026-10-29 11:00 omi-agent-security-reviewer (claude):
> ```
> VERDICT: PASS
> - src/omi/install.py:312,317 A corrupt `settings_before` in `~/.omi/install-user.json` makes `install-user --remove` crash with a raw `binascii.Error` traceback instead of an `OMI:` error | why: manifest validation checks only types, and `cli.py` catches only OSError/UnicodeError, not ValueError | verified: ran install, set `settings_before` to "!!!notbase64", ran `--remove` and got the traceback -> validate base64 in the manifest check, or catch ValueError in `cli.py`.
> - src/omi/install.py:362 Skills are written before the manifest, so an OSError partway through leaves skill files with no manifest | why: a later install records those omi files as the user's own "before" content, and `--remove` then restores them instead of deleting them | verified: code read only -> write the manifest first, or roll back on failure.
> UNVERIFIED: Windows host run (AC5) was not possible in this container; the Coordinator needs to run it.
> ```
> `python3 tests/test_omi.py` passed on Linux: it exited 0 and printed ok. I found no secret exposure, path escape or injection. Manifest paths are confined to `.claude/skills` and to the `.claude`, `.codex` and `.omi` directories. The change stays within the task scope.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 12 | 7452 | 209864 | 95s | - | n/a |
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 1683090 | 11845 | 1606912 | 415s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 2599 | 90356 | 248s | - | PASS dc1c949 |
| omi-agent-security-reviewer | claude-sonnet-5-5 | medium | 12 | 3126 | 223149 | 252s | 2/2 omi-skill-diff-security-review omi-skill-ci-workflow-audit | PASS dc1c949 |
