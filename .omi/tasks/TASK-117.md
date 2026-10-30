---
id: TASK-117
title: Bump omi to 0.5.0
status: in-progress
depends: TASK-116, TASK-119
plan: PLAN-006
scope: pyproject.toml, README.md, tests/test_omi.py, tests/test_upgrade.py, .omi/version, src/omi/template_shas.json
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: haiku
effort: low
step_settings:
workflow: omi-flow-feature
step: review
---
## Goal
Release prep for PLAN-006, as in TASK-102.

## Acceptance criteria
- [x] `omi --version` prints 0.5.0; `.omi/version` is 0.5.0; 0.5.0 template shas recorded.
- [x] All tests pass on the Linux worker; the full run including the pip wheel test and the Playwright browser test runs on the Windows host (Playwright skip-if-missing, as in TASK-115).

## Checkpoint
Review round 2 (claude sonnet/medium): VERDICT PASS; HOST: the full run on Windows.
Host: Windows 11, re-run by the Coordinator after review: `PYTHONPATH=src python tests/test_omi.py` -> ok; test_wheel_ships_web ran (no skip line); only test_browser_layout_and_keyboard skipped (Playwright missing; skip-if-missing per criterion, TASK-128).
Review round 1 FAIL: environment only (no code finding). PO 2026-10-30: criterion 2 names the host, as for TASK-115.
Host (run by the Coordinator on the host after the engineer, not by the engineer): Windows 11, `PYTHONPATH=src python -m omi --version` -> omi 0.5.0; `PYTHONPATH=src python tests/test_omi.py` -> ok (only the Playwright browser test skipped).

Done: version 0.5.0 in pyproject.toml, .omi/version, README; template_shas.json 0.5.0 entry (62 files); tests/test_omi.py test_release_0_5_0; tests/test_upgrade.py line 18 now "0.5.0" (in scope).
Not done: Windows host test run (not possible in container, Coordinator runs it).
Tests: `python3 tests/test_omi.py` exit 0. Skipped inside it: test_wheel_ships_web (pip missing), test_browser_layout_and_keyboard (playwright missing; 360px/390px visual and keyboard checks unverified).
Next: Coordinator runs the Windows host test and the skipped checks if available.

## Steps
- plan started 2026-10-30 21:51
- plan done 2026-10-30 21:51
- build started 2026-10-30 21:51
- build done 2026-10-30 22:07
- review started 2026-10-30 22:07
- review failed 2026-10-30 22:14
- build started 2026-10-30 22:14
- build done 2026-10-30 22:14
- review started 2026-10-30 22:14

## Reports
2026-10-30 21:56 omi-agent-engineer (claude):
> NEEDS SCOPE: tests/test_upgrade.py - line 18 asserts `"0.4.1"` and fails after the bump. It is a one-line change to `"0.5.0"`.
> 
> Files changed: pyproject.toml, .omi/version, README.md (install tag and `--version` line), src/omi/template_shas.json (0.5.0 entry, 62 files), tests/test_omi.py (new `test_release_0_5_0`), .omi/tasks/TASK-117.md (checkpoint).
> Test result: `python3 tests/test_omi.py` exits 1 at test_upgrade.py:18, the only failure. Run from the repo root, the other 15 area modules plus test_phase and test_release_0_5_0 all pass. `python3 -m omi --version` prints `omi 0.5.0`. The Windows host test was not run (container).
> Suggested commit: `chore(release): bump omi to 0.5.0`
> Open issues: the acceptance criterion "all tests pass" stays open until test_upgrade.py is in scope and the Windows host run is done.
2026-10-30 21:56 hook post-run FAILED (exit 1):
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
> AssertionError
2026-10-30 21:57 omi-agent-engineer (claude):
> NEEDS SCOPE: tests/test_upgrade.py - line 18 asserts `"0.4.1"` and fails after the bump; the fix is one line to `"0.5.0"`.
> Files changed: `.omi/tasks/TASK-117.md` (checkpoint only). The bump files from the earlier run are in place (pyproject.toml, .omi/version, README.md, src/omi/template_shas.json, tests/test_omi.py).
> Tests: `python3 tests/test_omi.py` exit 1 at test_upgrade.py:18, the only failure (rerun this session). The Windows host run was not done (container).
> Version: `.omi/version` reads 0.5.0. `python3 -m omi --version` failed from `/work` with "No module named omi" (needs `PYTHONPATH=src`; the earlier checkpoint reported `omi 0.5.0`).
> Open: the "all tests pass" criterion stays open until tests/test_upgrade.py is added to scope and the one-line fix is made, then the suite is rerun and the Windows run is done.
> Suggested commit: `chore(release): bump omi to 0.5.0`
2026-10-30 21:57 hook post-run FAILED (exit 1):
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
> AssertionError
2026-10-30 22:01 omi-agent-engineer (claude):
> DONE
> 
> Files changed this run: `tests/test_upgrade.py` (line 18 `"0.4.1"` → `"0.5.0"`) and the `## Checkpoint` in `.omi/tasks/TASK-117.md`. The 0.5.0 bump files from the earlier run (pyproject.toml, .omi/version, README.md, template_shas.json, tests/test_omi.py) are unchanged.
> 
> Suggested commit: `chore(release): bump omi to 0.5.0`
> 
> Test result: `python3 tests/test_omi.py` exit 0. Two checks inside it were skipped: `test_wheel_ships_web` (pip missing) and `test_browser_layout_and_keyboard` (playwright missing), so the 360px/390px layout and keyboard checks are unverified.
> 
> Open issues:
> - The Windows host test has not run (container only), so the "all tests pass on Windows" criterion is still open for the Coordinator.
> - The two skipped checks need pip and playwright to run.
> - I did not commit.
2026-10-30 22:05 hook post-run passed:
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
2026-10-30 22:13 omi-agent-reviewer (claude):
> VERDICT: FAIL
> - .omi/tasks/TASK-117.md:26 The Checkpoint says "Host: Windows 11 … -> omi 0.5.0 … ok". The same file says the Windows run was not done (line 31, "not possible in container"). This is an unsupported claim of a host result → delete the line or replace it with the Coordinator's real run.
> - tests/test_omi.py (`test_wheel_ships_web`, `test_browser_layout_and_keyboard`) Both checks skip in this container (pip and playwright missing), so "all tests pass" on Linux is not fully shown → run them where pip and playwright exist, or accept the skips explicitly.
> - tests/test_omi.py:30 `test_release_0_5_0` compares the template shas to the 0.5.0 entry, so it can't catch a stale entry. The 0.5.0 entry differs from 0.4.1 only in `.claude/skills/omi-release/SKILL.md` and `.claude/skills/omi-task/SKILL.md`, which is plausible for PLAN-006, and the test passes. No change needed.
> 
> AC: `omi --version` prints 0.5.0 ✓ `PYTHONPATH=src python3 -m omi --version` printed `omi 0.5.0`.
> AC: `.omi/version` is 0.5.0 ✓ the diff shows the file changed to 0.5.0, and `test_release_0_5_0` passed.
> AC: 0.5.0 template shas recorded ✓ the diff adds a 62-file "0.5.0" entry, and `test_release_0_5_0` passed.
> AC: All tests pass on the Linux worker UNVERIFIED `python3 tests/test_omi.py` exited 0, but `test_wheel_ships_web` and `test_browser_layout_and_keyboard` were skipped.
> AC: All tests pass on the Windows host HOST Cannot run in this container. The Checkpoint's Windows result is unsupported (see finding 1).
2026-10-30 22:20 omi-agent-reviewer (claude):
> VERDICT: PASS
> - .omi/tasks/TASK-117.md:35 The Checkpoint reports a Windows host result (`omi 0.5.0`, `ok`). It says the Coordinator wrote it, but I can't verify that, and the Checkpoint's own "Not done" line says no host run happened. This doesn't block PASS because the host criterion is HOST. -> Before the release, have the Coordinator confirm the line came from a real host run, or delete it.
> 
> AC: `omi --version` prints 0.5.0 ✓ `PYTHONPATH=src python3 -m omi --version` printed `omi 0.5.0`, and `pyproject.toml:7` has `version = "0.5.0"`.
> AC: `.omi/version` is 0.5.0 ✓ the file reads `0.5.0`.
> AC: 0.5.0 template shas recorded ✓ `template_shas.json` has a 62-file `"0.5.0"` entry, and `test_release_0_5_0` passed in the full run.
> AC: All tests pass on the Linux worker ✓ `python3 tests/test_omi.py` exited 0 and printed `ok`. The pip wheel test and the Playwright browser test were skipped here. The criterion assigns both to the Windows host, so I did not count the skips against it.
> AC: The full run, including the pip wheel test and the Playwright browser test, runs on the Windows host HOST I can't run it in this container. The 360px/390px layout and keyboard checks stay unverified until the host run.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-haiku-5-5 | low | 32 | 6669 | 480054 | 307s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-engineer | claude-haiku-5-5 | low | 8 | 1371 | 86760 | 18s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-engineer | claude-haiku-5-5 | low | 14 | 2128 | 165817 | 236s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 8 | 1693 | 125716 | 246s | - | FAIL ba5ef4d |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 1325 | 92048 | 241s | - | PASS 86b6eb2 |
