---
id: TASK-112
title: Group src/omi into subpackages without behaviour change
status: in-progress
depends: TASK-109
plan: PLAN-006
scope: src/omi/**, tests/**, .omi/rules/omi-modules.md, .omi/rules/CATALOG.md, pyproject.toml, .omi/tasks/TASK-112.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: opus
effort: high
step_settings:
workflow: omi-flow-refactor
step: refactor
---
## Goal
The flat 18-module `src/omi` becomes a few subpackages by responsibility (for example state, worker, project, setup), so the board and later work land in a clear place. Behaviour, CLI and the `python -m omi` entry stay identical.

## Acceptance criteria
- [x] Every module sits in a subpackage named for one responsibility; `attach` no longer lives in the upgrade module; `__init__.py` stays the package surface.
- [x] `.omi/rules/omi-modules.md` describes the new layout and layer order; `python -m omi rules` regenerates the catalog.
- [ ] Same test suite passes before and after with only import-path and patch-target edits; template files and `template_shas.json` unchanged; `pip install .` still ships the template.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Review round 1 FAIL: only `pip install .` UNVERIFIED (no pip in the read-only container); no code finding. Verified on the host instead, no code change:
Host: python -m venv <tmp> && <tmp>/Scripts/python -m pip install . -> installed; `omi --version` -> omi 0.4.0; installed package dirs app, common, project, setup, state, template, worker; template/AGENTS.md present, 111 template entries; `omi init` in a new git repo -> `tools: git ok, gh ok, docker ok, claude ok, codex ok`.
Host: python tests/test_omi.py (Windows host, worktree) -> ok, exit 0; same 97 test names as development.
Baseline (Coordinator, development 08e0bf1): `python tests/test_omi.py` -> ok on the Windows host and CI; 97 `def test_` functions across tests/test_*.py. Tests may change only import paths and patch targets (`omi.<new.module>.<name>`).
Done: Moved 16 implementation modules into app/common/state/project/worker/setup and extracted setup.attach. Root main/version exports and the unchanged module entry remain. Adjusted template/hash/version resource paths; updated module rules and regenerated the catalog with `PYTHONPATH=src python3 -m omi rules`. All 97 existing tests retained with only module-reference/patch-target edits; suite runner unchanged. Temporary verification files removed; no commit made.
Not done: Post-change Windows host suite and real pip build/install verification require the Coordinator's environment. No implementation issue remains known.
Tests: `TMPDIR=/work/tests/.task112/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 python3 tests/test_omi.py` -> `ok`, exit 0 on Linux/Python 3.13.5; no symlink-unavailable skips were reported. Ad hoc assertions passed for module layout/public surface, unchanged function/class ASTs except required extraction/path edits, reference-only test changes, documented import layer order, source version/resource paths, reproducible catalog, and package-data coverage of all 68 assets. Template files and template_shas.json were checked byte-identical before and after the suite. An isolated installed-layout fixture passed imports, metadata version, template/hash lookup and `python -m omi --version`; this was not a pip build/install. The redundant local baseline attempt was interrupted due to slow mounted filesystem; the recorded green Coordinator baseline is the before result.
Unavailable checks: `python3 -m pip install . --target tests/.task112/install` failed before installation because pip is absent; ensurepip is also absent. Downloads from PyPI and bootstrap.pypa.io were blocked by the container network policy. Windows host tests were not run in this Linux container.
Next: Coordinator reviews the diff, runs `python tests/test_omi.py` on Windows and verifies `pip install .` includes the template, then completes acceptance and commits on the host. Suggested commit: `refactor(omi): group modules into responsibility subpackages`.

## Steps
- plan started 2026-10-29 16:47
- plan done 2026-10-29 16:47
- baseline started 2026-10-29 16:47
- baseline skipped 2026-10-29 16:47: baseline green: python tests/test_omi.py ok on host and CI at 08e0bf1; test count recorded in Checkpoint
- refactor started 2026-10-29 16:47
- refactor done 2026-10-29 17:19
- review started 2026-10-29 17:19
- review failed 2026-10-29 17:30
- refactor started 2026-10-29 17:30

## Reports
2026-10-29 17:08 omi-agent-engineer (codex):
> BLOCKED — implementation complete; host/install verification pending.
> 
> - Changed: `src/omi/**`, test module references, module rules/catalog, and task checkpoint.
> - Suggested commit: `refactor(omi): group modules into responsibility subpackages`
> - Tests: `python3 tests/test_omi.py` → `ok` on Linux; structural/resource checks passed.
> - Open: Windows tests not run; real pip installation blocked by missing tooling and network policy.
> - Templates/hashes unchanged. Temporary files removed. No commit made.
2026-10-29 17:14 hook post-run passed:
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
2026-10-29 17:25 omi-agent-reviewer (codex):
> VERDICT: FAIL
> AC: Modules grouped by responsibility; attach extracted; package surface retained ✓ Implementation diff and import checks confirm all three.
> AC: Layout and layer order documented; rules catalog regenerates ✓ Generated content matches CATALOG.md with writes intercepted.
> AC: Same suite before and after; only import/patch edits ✓ Recorded baseline passed; current suite exits 0 with `ok`; all 97 test functions retained with reference-only edits.
> AC: Templates and template_shas.json unchanged ✓ Neither appears in the diff.
> AC: pip install . ships the template UNVERIFIED Installation could not execute: `No module named pip`.
> AC: All tests pass on Linux worker ✓ `python3 tests/test_omi.py` exits 0 with `ok`.
> AC: All tests pass on Windows host HOST Requires execution on the Windows host.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | gpt-6-astra (codex) | high | 3876813 | 18658 | 3806720 | 1230s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | gpt-6.1-sol (codex) | medium | 1501907 | 4181 | 1445504 | 300s | 1/1 omi-skill-simplify-review | FAIL e843e0e |
