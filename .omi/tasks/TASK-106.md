---
id: TASK-106
title: Repo rule for the src/omi module structure
status: in-progress
depends: TASK-104
plan: PLAN-004
scope: .omi/rules/omi-modules.md, .omi/rules/CATALOG.md
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: haiku
effort: low
step_settings:
workflow: omi-flow-feature
step: build
---
## Goal
The module rules chosen in TASK-104 (decisions.md 2026-10-28) live only in decisions.md, which agents do not read. A rule in `.omi/rules` reaches every task whose scope touches `src/omi/*.py` through `omi run`, so PLAN-004 code follows the split without restating it per task. Repo-only: the template (`src/omi/template/**`) is not changed, user projects do not get it.

## Acceptance criteria
- [ ] `.omi/rules/omi-modules.md` with frontmatter `id`, `summary`, `applies: src/omi/*.py`, at most ~200 tokens, says: modules call each other as `from . import x` then `x.name(...)`, never `from .x import name`; imports only go down the layer order of the current graph, cli > run > hooks > docker > tasks/upgrade > workflows > catalogs > tools/creds/scope > core/github (no import inside a function to dodge a cycle); no module over ~600 lines; a new responsibility gets a new module; `__init__.py` stays the package surface; tests patch the defining module (`omi.<module>.<name>`).
- [ ] `.omi/rules/CATALOG.md` regenerated with `python -m omi rules`; `omi.catalogs.task_rules` picks the rule for `src/omi/run.py` and not for `tests/test_omi.py` (shown by the command output in the report).
- [ ] All tests pass on the Linux worker and on the Windows host.

## Checkpoint
Done: .omi/rules/omi-modules.md written (~175 tokens); CATALOG.md regenerated with `PYTHONPATH=src python3 -m omi rules` (6 rules, omi-modules listed)
Not done: Windows host test run (AC3 host part) - Coordinator to run
Tests: `python3 tests/test_omi.py` exit 0 ("ok") on Linux worker. task_rules: src/omi/run.py -> omi-modules.md, python.md; tests/test_omi.py -> python.md only
Next: Coordinator runs tests on Windows host, then commits

Review round 1 FAIL: (Coordinator) omi-modules.md says `__init__.py` must not re-export names, but src/omi/__init__.py re-exports `main` and `version` from cli/core and that IS the package surface. Reword: `__init__.py` stays the package surface: only re-exports the public names (`main`, `version`); no logic there. Regenerate CATALOG.md if the summary changes.

## Steps
- plan started 2026-10-28 20:57
- plan done 2026-10-28 20:57
- build started 2026-10-28 20:57
- build done 2026-10-28 21:06
- review started 2026-10-28 21:06
- review failed 2026-10-28 21:11
- build started 2026-10-28 21:11

## Reports
2026-10-28 21:03 omi-agent-engineer (claude):
> DONE
> Files: `.omi/rules/omi-modules.md` (new, ~175 tokens, `applies: src/omi/*.py`), `.omi/rules/CATALOG.md` (regenerated), `.omi/tasks/TASK-106.md` (checkpoint).
> Rule selection: `src/omi/run.py` → `omi-modules.md`, `python.md`. `tests/test_omi.py` → `python.md` only (no `omi-modules`).
> Tests: `python3 tests/test_omi.py` exit 0, prints `ok`, on the Linux worker. Windows host not run; the Coordinator must run it (AC3).
> Suggested commit: `docs(rules): add omi-modules rule for src/omi structure`
> Open issues: `python -m omi` needs `PYTHONPATH=src` in this container. The first run of the test suite exceeded 120s and was backgrounded; the rerun finished in under 500s.
2026-10-28 21:05 hook post-run passed:
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
2026-10-28 21:11 omi-agent-reviewer (claude):
> ```
> VERDICT: PASS
> AC: omi-modules.md has the required frontmatter and covers every listed point ✓ The file has `id`, `summary` and `applies: src/omi/*.py`, and is ~175 tokens (CATALOG reports it). It states the `from . import x` rule, the layer order, no function-level imports, the ~600-line cap, new responsibility means new module, `__init__.py` as the package surface, and patching `omi.<module>.<name>`.
> AC: CATALOG.md regenerated; task_rules picks the rule for src/omi/run.py and not for tests/test_omi.py ✓ I called `catalogs.task_rules` myself. `['src/omi/run.py']` returned `['omi-modules.md','python.md']`, and `['tests/test_omi.py']` returned `['python.md']`. Re-running `python -m omi rules` gives the same CATALOG content as the diff, with 6 rules including omi-modules.
> AC: All tests pass on the Linux worker ✓ `python3 tests/test_omi.py` exited 0 and printed "ok".
> AC: All tests pass on the Windows host HOST Windows host run, left to the Coordinator.
> ```
> 
> The diff stays within scope. The only other file it touches is TASK-106.md, the task's own checkpoint file.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-haiku-5-5 | low | 18 | 2902 | 236724 | 333s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 12 | 1276 | 139557 | 263s | - | PASS 93ea4fe |
