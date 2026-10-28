---
id: TASK-104
title: Split src/omi/__init__.py into modules by responsibility
status: in-progress
depends: TASK-103
plan: PLAN-003
scope: src/omi/*.py, src/omi/*/*.py, tests/test_omi.py, pyproject.toml, .omi/skills/CATALOG.md, .omi/agents/CATALOG.md, .omi/rules/CATALOG.md
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: opus
effort: high
step_settings:
workflow: omi-flow-refactor
step: baseline
---
## Goal
`src/omi/__init__.py` is one 2640-line file. Every code task must put the whole file in `scope`, so scopes are coarse, parallel tasks always conflict and agents read more than they need. The PO asked (2026-10-28) for a clean, senior-grade structure before PLAN-004 adds detached mode. Behaviour stays identical; this is a move, not a rewrite.

Design rules: one module per responsibility (for example cli, config/paths, tasks and steps, catalogs, run/worker/docker, hooks, git/worktree, upgrade/template); a design pattern only where it removes real duplication in the current code (e.g. one adapter per agent tool if claude/codex branches repeat); no abstraction with a single implementation, no new dependency, stdlib only.

## Acceptance criteria
- [ ] `src/omi/__init__.py` keeps only the package surface (re-exports, version); no module over ~600 lines; no import cycles (`python -c "import omi"` and each module imports on its own).
- [ ] Behaviour unchanged: `python -m omi <cmd>` output and exit codes are the same for every command; the test suite passes with only mechanical test edits (import paths, monkeypatch targets), no assertion removed or weakened.
- [ ] Nothing under `src/omi/template/**` changes; `template_shas.json` unchanged; the built package still ships the template (`pip install .` in a temp venv, then `python -m omi status` in a temp repo works).
- [ ] All tests pass on the Linux worker and on the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next: PO approved option A from the architect report below (decisions.md 2026-10-28). Baseline run: confirm tests green before any change; add characterization tests in tests/test_omi.py (the only place that survives between runs) so every USAGE command's exit code and key output is pinned; no src change. Refactor run 1: extract core, catalogs, workflows, upgrade, tasks, github. Refactor run 2: extract creds, tools, docker, hooks, run, cli; reduce __init__ to the package surface; `grep -nE "omi\.[A-Za-z_]+ *=[^=]" tests/test_omi.py` shows only omi.<module>.<name>; `python -c "import omi.<m>"` per module; `pip install .` in a temp venv + `python -m omi status` in a temp repo.
## Steps
- plan started 2026-10-28 15:04
- plan done 2026-10-28 15:07
- baseline started 2026-10-28 15:07

## Reports
2026-10-28 15:06 omi-agent-architect (claude):
> ```
> RECOMMEND: A - flat sibling modules where code always calls other modules through the module name (`from . import core` then `core.git(...)`, never `from .core import git`), so each test patch has one target (the module that defines the name) and still reaches every caller after the move.
> OPTIONS: A: flat modules, module-qualified calls, tests patch the defining module (e.g. `omi.core.WINDOWS`) / pro: behaviour is a pure move, test edits are mechanical, no cycles if layered / con: every reference in moved code and in the patch lines (about 25 names) needs a prefix; B: `from .x import name` plus re-exporting everything from `__init__` / pro: smallest diff / con: `omi.WINDOWS=`, `omi.git=`, `omi.egress=` and similar patches silently stop working (each module has its own copy of the name), so tests could pass while testing nothing; C: subpackages plus a claude/codex adapter class / pro: removes the 19 scattered `tool==` branches / con: that is a rewrite (the AC asks for a move), more risk; do it as a follow-up after PLAN-004 if the branches keep growing.
> [... truncated ...]
> ```

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 16 | 7738 | 242377 | 85s | - | n/a |
