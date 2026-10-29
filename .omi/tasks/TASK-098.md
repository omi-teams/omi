---
id: TASK-098
title: omi attach: register a code repo in the omi-state repo
status: in-progress
depends: TASK-097
plan: PLAN-004
scope: src/omi/state.py, src/omi/upgrade.py, src/omi/cli.py, tests/test_omi.py, README.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature
step: accept
---
## Goal
`omi attach [<repo path>]` turns any git repo into a detached omi project without touching it.

## Acceptance criteria
- [x] `omi attach` in a code repo with an `origin` creates `projects/<name>/` in the state dir from the same template `omi init` uses (`.omi/`, `docker/`, hooks; no `AGENTS.md`/`.claude` there), writes `project.json`, commits it in the state repo, and never writes in the code repo. `<name>` defaults to the repo name; an existing one is refused unless it is the same URL. Tested.
- [x] No state dir yet: `omi attach --state <git url>` clones it to `~/.omi/state` (or `OMI_STATE`); with no URL it `git init`s one and prints how to add a private remote. Tested with a local bare repo as remote.
- [x] A second clone of the state repo (another `OMI_STATE`) resolves the same project for a fresh clone of the code repo in another dir. Tested.
- [x] A malformed or duplicate `project.json` makes every command exit non-zero with a one-line `OMI:` message naming the file, not a `ValueError` traceback (follow-up from TASK-097, decisions 2026-10-28). Tested.
- [x] `omi attach` is listed in USAGE and pinned in `test_cli_characterization` (exit codes and key output).
- [x] All tests pass on the Linux worker and the Windows host; in-repo mode behaviour is unchanged (existing tests untouched or only extended).

## Checkpoint
Fix round 1 (PO at accept, reviewer PASS findings):
- src/omi/upgrade.py attach: if the state commit (or init) fails, remove the new projects/<name> dir and unstage it, so a rerun of omi attach works; test with a state repo whose commit fails (e.g. no git user.name).
- src/omi/state.py resolve (and upgrade.py attach): a malformed code-repo origin URL must exit with a one-line OMI: message (StateError), not a ValueError traceback; test via the CLI.
Done: Implemented omi attach, portable origin registry, state clone/init and isolated project commits; detached init/upgrade exclude AGENTS.md and .claude; README, USAGE and acceptance tests updated.
Not done: Windows host validation (not available in this Linux container).
Tests: TMPDIR=/work/.tmp-task-098 python3 -u tests/test_omi.py -> exit 0, final output ok; no explicit test skips. Covers registration/template/code bytes unchanged, URL identity/collision, unrelated staged files, local bare state clone, fresh-clone resolution, default state home, every CLI command rejecting malformed/duplicate registries, and CLI characterization; existing regression suite also ran.
Next: Coordinator reviews the diff and runs python3 tests/test_omi.py on the Windows host before committing.

Host: python tests/test_omi.py (Windows host, worktree at commit feat: add detached project attachment) -> exit 0, ok

## Steps
- plan started 2026-10-29 09:15
- plan done 2026-10-29 09:15
- build started 2026-10-29 09:15
- build done 2026-10-29 09:30
- review started 2026-10-29 09:30
- review done 2026-10-29 09:35
- accept started 2026-10-29 09:35
- PO at accept: fix the two reviewer findings in one round, then merge

## Reports
2026-10-29 09:26 omi-agent-engineer (codex):
> DONE
> Files: `src/omi/{state,upgrade,cli}.py`, `tests/test_omi.py`, `README.md`, `.omi/tasks/TASK-098.md`.
> Commit: `feat: add detached project attachment`
> Tests: `python3 -u tests/test_omi.py` → exit 0, `ok`; no explicit test skips.
> Open: Windows host validation pending. Checkpoint updated; no worktree commit made.
2026-10-29 09:29 hook post-run passed:
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
2026-10-29 09:35 omi-agent-reviewer (claude):
> VERDICT: PASS
> - src/omi/upgrade.py:320 If the state commit fails (for example no git `user.name`), `projects/<name>` is left written and staged. The next `omi attach` then fails with "project already exists; origin differs or project.json is missing" and needs manual cleanup. -> Remove the project dir and unstage it on failure, or run the preflight check before `init`.
> - src/omi/state.py:69 `normalise_url(remote)` on the code repo's own origin is not wrapped in `StateError`. A malformed origin URL gives a `ValueError` traceback instead of a one-line `OMI:` message. `upgrade.py:279` has the same gap. -> Wrap it and raise `StateError`.
> 
> AC: attach creates `projects/<name>/` from the template without `AGENTS.md` or `.claude`, writes `project.json`, commits in the state repo, leaves the code repo untouched, refuses a name collision unless the URL matches ✓ `test_attach_registration` passed (`python3 tests/test_omi.py` exits 0 and prints `ok`). It checks the code repo bytes are unchanged, the commit subject, the collision refusal and a pre-staged unrelated file.
> AC: `--state <url>` clones, no URL runs `git init` and prints the private-remote hint, `OMI_STATE` and the default `~/.omi/state` both work ✓ `test_attach_clone_portability` uses a local bare repo as remote and a patched home.
> AC: a second state clone resolves the same project for a fresh code clone ✓ the same test checks `state.resolve` and "already attached" using `second_home` and `fresh`.
> AC: a malformed or duplicate `project.json` makes every command exit with a one-line `OMI:` message naming the file ✓ `test_invalid_registry_cli` loops 24 commands over 6 bad inputs, plus a subprocess run that checks for no traceback.
> AC: `omi attach` is in USAGE and pinned in `test_cli_characterization` ✓ the test checks the usage list, the no-origin error, the usage error and the already-attached output.
> [... truncated ...]
> AC: all tests pass on the Windows host HOST the task text names the Windows host, which this container cannot run.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 1878945 | 17940 | 1831552 | 672s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 2049 | 86308 | 242s | - | PASS ecdfb0b |
