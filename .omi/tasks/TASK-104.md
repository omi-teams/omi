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
step:
---
## Goal
`src/omi/__init__.py` is one 2640-line file. Every code task must put the whole file in `scope`, so scopes are coarse, parallel tasks always conflict and agents read more than they need. The PO asked (2026-10-28) for a clean, senior-grade structure before PLAN-004 adds detached mode. Behaviour stays identical; this is a move, not a rewrite.

Design rules: one module per responsibility (for example cli, config/paths, tasks and steps, catalogs, run/worker/docker, hooks, git/worktree, upgrade/template); a design pattern only where it removes real duplication in the current code (e.g. one adapter per agent tool if claude/codex branches repeat); no abstraction with a single implementation, no new dependency, stdlib only.

## Acceptance criteria
- [ ] `src/omi/__init__.py` keeps only the package surface (re-exports, version); no module over ~600 lines; no import cycles (`python -c "import omi"` and each module imports on its own).
- [ ] Behaviour unchanged: `python -m omi <cmd>` output and exit codes are the same for every command; the test suite passes with only mechanical test edits (import paths, monkeypatch targets), no assertion removed or weakened.
- [ ] Nothing under `src/omi/template/**` changes; `template_shas.json` unchanged; the built package still ships the template: on the host, `pip install .` in a temp venv, then `python -m omi status` in a temp repo works.
- [ ] All tests pass on the Linux worker and on the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:
