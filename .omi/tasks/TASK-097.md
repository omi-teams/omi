---
id: TASK-097
title: Detached state root: .omi state outside the code repo
status: in-progress
depends: TASK-095, TASK-106
plan: PLAN-004
scope: src/omi/*.py, tests/test_omi.py, docs/specs/detached-mode.md
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
- [ ] A project is detached when `~/.omi/state/projects/<name>/project.json` names the code repo's `origin` URL (normalised: https/ssh, trailing `.git`); `OMI_STATE` overrides `~/.omi/state`. One function in a new `src/omi/state.py` resolves (state root, code root); every command uses it. Tested with temp dirs.
- [ ] In a detached project, `status`, `step`, `plans`, `skills check`, `hook` and `run` read and write only the state dir; git branches, worktrees (`../<repo>.wt/<ID>`) and the scope check act on the code repo; the code repo's `git status` stays clean after a full `omi step` cycle. Tested with real git.
- [ ] `omi run` gives the agent the task file and catalogs from the state dir inside the container (mounted read-only next to the worktree); the engineer never writes into the state dir. Tested.
- [ ] All tests pass on the Linux worker and the Windows host; in-repo mode behaviour is unchanged (existing tests untouched or only extended).

## Checkpoint
Done:
Not done:
Tests:
Next: PO chose architect option B as one task (no E1/E2 split). Add `state` to the layer order in .omi/rules/omi-modules.md (tools/creds/scope > state > core/github) and regenerate the catalog with `python -m omi rules`.

## Steps
- plan started 2026-10-28 21:26
- plan done 2026-10-28 21:26
- architect started 2026-10-28 21:26
- architect done 2026-10-28 21:29
- build started 2026-10-28 21:29

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

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 18 | 6400 | 354949 | 77s | - | n/a |
