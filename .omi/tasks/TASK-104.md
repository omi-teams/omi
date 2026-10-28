---
id: TASK-104
title: Split src/omi/__init__.py into modules by responsibility
status: done
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
step: accept
---
## Goal
`src/omi/__init__.py` is one 2640-line file. Every code task must put the whole file in `scope`, so scopes are coarse, parallel tasks always conflict and agents read more than they need. The PO asked (2026-10-28) for a clean, senior-grade structure before PLAN-004 adds detached mode. Behaviour stays identical; this is a move, not a rewrite.

Design rules: one module per responsibility (for example cli, config/paths, tasks and steps, catalogs, run/worker/docker, hooks, git/worktree, upgrade/template); a design pattern only where it removes real duplication in the current code (e.g. one adapter per agent tool if claude/codex branches repeat); no abstraction with a single implementation, no new dependency, stdlib only.

## Acceptance criteria
- [x] `src/omi/__init__.py` keeps only the package surface (re-exports, version); no module over ~600 lines; no import cycles (`python -c "import omi"` and each module imports on its own).
- [x] Behaviour unchanged: `python -m omi <cmd>` output and exit codes are the same for every command; the test suite passes with only mechanical test edits (import paths, monkeypatch targets), no assertion removed or weakened.
- [x] Nothing under `src/omi/template/**` changes; `template_shas.json` unchanged; the built package still ships the template: on the host, `pip install .` in a temp venv, then `python -m omi status` in a temp repo works.
- [x] All tests pass on the Linux worker and on the Windows host.

## Checkpoint
Review round 1 FAIL: only AC3 `pip install .` UNVERIFIED (no pip/venv in the container); PO 2026-10-28: AC3 is a host check, evidence in the Host: line below; no code change.
Done (refactor, runs 1+2 in one go): `src/omi/__init__.py` (2651 lines) split by a scripted pure move into 13 flat modules, `__init__` = docstring + `from .cli import main`, `from .core import version`. Layers (no cycles): core <- tools, creds, scope, github(stdlib) <- catalogs <- workflows <- tasks, upgrade; docker <- core, creds; hooks <- docker, tasks; run <- all but cli/upgrade/github; cli on top. Lines: core 76, hooks 65, scope 103, workflows 120, creds 143, cli 155, github 174, tools 230, docker 276, upgrade 288, tasks 359, catalogs 371, run 408. Cross-module calls are always `module.name` (option A); names inside a module stay bare. No src/omi/template/** or template_shas.json change; pyproject.toml unchanged (`omi:main` still re-exported). No claude/codex adapter (option C left as follow-up).
Proof of pure move: AST of all 211 top-level statements equals the original once `module.` prefixes are stripped; 110/110 comment lines kept; symtable check: no undefined global in any module.
Tests (mechanical edits only): `omi.<name>` -> `omi.<module>.<name>`; `omi.<stdlib>` (os, sys, subprocess, shutil, contextlib, importlib, time, getpass, tomllib) -> the stdlib module, imported in the test; the version test patches `omi.core.__file__` (path ends `omi/core.py`). No assertion changed. `grep -nE "omi\.[A-Za-z_]+ *=[^=]" tests/test_omi.py` shows only omi.<module>.<name>.
Tests: `python3 tests/test_omi.py` -> ok (exit 0) on Linux, incl. test_cli_characterization. `python -c "import omi.<m>"` ok for all 13; each module imported without `__init__` loads only its own layer.
Not run here: `pip install .` in a temp venv (container has no pip/venv/setuptools). Substitute: package files + template + a dist-info copied to a temp site dir, then `python -m omi init` and `python -m omi status` in a temp git repo -> exit 0, version 0.3.1 from metadata. Windows host run pending.
Next: Coordinator host checks: `python tests/test_omi.py` on Windows; `pip install .` in a temp venv + `python -m omi status` in a temp repo.

## Steps
- plan started 2026-10-28 15:04
- plan done 2026-10-28 15:07
- baseline started 2026-10-28 15:07
- baseline done 2026-10-28 15:24
- refactor started 2026-10-28 15:24
- refactor done 2026-10-28 15:38
- review started 2026-10-28 15:38
- review done 2026-10-28 16:15
- accept started 2026-10-28 16:15

## Reports
2026-10-28 15:06 omi-agent-architect (claude):
> ```
> RECOMMEND: A - flat sibling modules where code always calls other modules through the module name (`from . import core` then `core.git(...)`, never `from .core import git`), so each test patch has one target (the module that defines the name) and still reaches every caller after the move.
> OPTIONS: A: flat modules, module-qualified calls, tests patch the defining module (e.g. `omi.core.WINDOWS`) / pro: behaviour is a pure move, test edits are mechanical, no cycles if layered / con: every reference in moved code and in the patch lines (about 25 names) needs a prefix; B: `from .x import name` plus re-exporting everything from `__init__` / pro: smallest diff / con: `omi.WINDOWS=`, `omi.git=`, `omi.egress=` and similar patches silently stop working (each module has its own copy of the name), so tests could pass while testing nothing; C: subpackages plus a claude/codex adapter class / pro: removes the 19 scattered `tool==` branches / con: that is a rewrite (the AC asks for a move), more risk; do it as a follow-up after PLAN-004 if the branches keep growing.
> [... truncated ...]
> ```
2026-10-28 15:15 omi-agent-engineer (claude):
> DONE (baseline step: characterization tests added, no `src/` changes)
> 
> - **Files changed:** `tests/test_omi.py` (new `test_cli_characterization`, registered in `__main__`) and the Checkpoint in `.omi/tasks/TASK-104.md`.
> - **Suggested commit:** `test(cli): pin exit codes and output of every omi command before the module split`
> - **What it does:** runs `python -m omi` as a subprocess with PATH limited to git's folder, so gh and docker are missing on Linux and Windows alike. It checks exact exit codes and output for every USAGE command, including the error paths and the step, parallel and guard sequences. It doesn't touch omi's internals, so it should survive the refactor without edits.
> - **Tests:** `python3 tests/test_omi.py` passed (exit 0, `ok`) on Linux before the change and again with the new test. I did not run it on the Windows host.
> - **Not covered by this test** (each needs docker, the network, a real worktree or Windows): `clean`, `upgrade --check` and real installs, the success paths of `run`/`hook`/`worker`, `token set` on Windows, and the hidden `template-shas`. The existing in-process tests still cover these.
> - **Open issue:** none.
2026-10-28 15:17 hook post-run passed:
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
2026-10-28 15:21 omi-agent-engineer (claude):
> DONE (baseline round 2: fixed the Windows host failure)
> - **Files changed:** `tests/test_omi.py` and the Checkpoint in `.omi/tasks/TASK-104.md`. No `src/` changes.
> - **The fix:** the `cli()` helper in `test_cli_characterization` now turns `\` into `/` in stdout and stderr before any assertion runs. That makes every path check in the test work with either separator: the CATALOG lines (where Windows failed), `stamp  .omi/version`, the init create/skip lines, and the path endings in the guard, step and worker messages.
> - **Why it hides nothing:** a grep of `src/omi/__init__.py` found no printed message that contains a literal backslash.
> - **Suggested commit:** `test(cli): normalise path separators in CLI characterization output`
> - **Tests:** `python3 tests/test_omi.py` passed on Linux (exit 0, `ok`). Windows has not been re-run yet; it needs the host check.
> - **Open issues:** none.
2026-10-28 15:23 hook post-run passed:
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
2026-10-28 15:34 omi-agent-engineer (claude):
> DONE. I split `src/omi/__init__.py` into 13 modules and kept the behaviour the same. I did both planned refactor runs in this one pass.
> - **Files changed:** `src/omi/__init__.py` now only re-exports `main` and `version`. The new modules are `core`, `tools`, `creds`, `github`, `catalogs`, `workflows`, `tasks`, `scope`, `upgrade`, `docker`, `hooks`, `run` and `cli`. Also changed: `tests/test_omi.py` and the Checkpoint in `.omi/tasks/TASK-104.md`. Nothing changed in the template, `template_shas.json` or `pyproject.toml`.
> - **Structure:** the largest module is `run.py` at 408 lines. Imports form a layered graph with no cycles. Code always calls another module through its name (`core.git(...)`), so each test patch has one target.
> - **Evidence it's a pure move:** all 211 top-level statements match the original once the module prefixes are stripped, and all 110 comment lines are kept.
> - **Test edits:** only renames. `omi.X` became `omi.<module>.X`, `omi.os` and the other standard-library references became plain imports, and the version test now patches `omi.core.__file__`. No assertion was removed or weakened.
> - **Tests:** `python3 tests/test_omi.py` passed on Linux (exit 0, `ok`), including `test_cli_characterization`. `python -c "import omi.<m>"` works for all 13 modules.
> - **Not run:** `pip install .`, because the container has no pip, venv or setuptools. As a substitute I copied the package files plus fake package metadata into a temp folder; `python -m omi init` and `python -m omi status` worked there (exit 0, version 0.3.1).
> - **Open:** the Windows test run and a real `pip install .` in a temp venv still need a host check.
> 
> Suggested commit: `refactor(omi): split __init__.py into modules by responsibility`
2026-10-28 15:37 hook post-run passed:
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
2026-10-28 15:43 omi-agent-reviewer (claude):
> VERDICT: FAIL
> - Task AC3: the `pip install .` check was not run. The container has no pip or setuptools, and `python3 -m venv` also fails there, so the built-package check is unverified. The worker's substitute (copying files plus fake metadata into a temp site dir) does not exercise setuptools packaging. `pyproject.toml` is unchanged and its package-data globs cover `template/**`, which makes a packaging failure unlikely. Run `pip install .` in a temp venv, then `python -m omi status` in a temp repo, on the host.
> 
> AC: `__init__.py` keeps only the package surface; no module over ~600 lines; no cycles ✓ `__init__.py` is 6 lines (docstring, `from .cli import main`, `from .core import version`). The largest module is `run.py` at 408 lines. All 13 modules import on their own under `python3 -I` with no error.
> AC: Behaviour unchanged; tests need only mechanical edits ✓ `python3 tests/test_omi.py` exits 0 and prints `ok`, including `test_cli_characterization`. I normalised the test diff by stripping the `omi.<module>.` prefixes. Every removed line reappears as a rename to `omi.<module>.X` or a plain stdlib reference. The only other change is the `omi.__file__` fixture path (`__init__.py` to `core.py`). I found no removed or weakened assertion.
> AC: Nothing under `template/**` changes, `template_shas.json` unchanged ✓ The diff touches no template path and no `template_shas.json`. `pyproject.toml` is untouched, and `omi:main` still resolves through the `__init__` re-export.
> AC: The built package ships the template (`pip install .` in a temp venv, then `python -m omi status`) UNVERIFIED No pip, setuptools or venv in the container; see the finding above.
> AC: All tests pass on the Linux worker ✓ and on the Windows host HOST The Linux run passed. The Windows host run is pending.
2026-10-28 16:15 omi-agent-reviewer (claude):
> VERDICT: PASS
> - No blocking findings.
> 
> AC: `__init__.py` keeps only the package surface; no module over ~600 lines; no cycles ✓ `__init__.py` is 6 lines (docstring plus the `main` and `version` re-exports). The largest module is `run.py` at 408 lines. All 13 modules import on their own under `python3 -I` with no error. Imports are all `from . import <module>`, layered, with no cycles.
> AC: Behaviour unchanged; only mechanical test edits ✓ `python3 tests/test_omi.py` exits 0 and prints `ok`, including `test_cli_characterization`. In the test diff, every removed line reappears with only its `omi.` prefix changed, or with `os`/`subprocess`/`time` and similar imported directly. The `__file__` fixture now ends in `core.py`. I found no removed or weakened assertion.
> AC: Nothing under `src/omi/template/**` changes, `template_shas.json` unchanged ✓ The diff lists no template path and no `template_shas.json`, and `pyproject.toml` is untouched. `omi:main` still resolves through the `__init__` re-export.
> AC: `pip install .` in a temp venv, then `python -m omi status` in a temp repo HOST The criterion names the host, and the container has no pip or venv. The worker's substitute run does not replace it; the PO already ruled this a host check.
> AC: Tests pass on the Linux worker ✓ and on the Windows host HOST The Linux run passed. The Windows run is pending on the host.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 16 | 7738 | 242377 | 85s | - | n/a |
| omi-agent-engineer | claude-opus-5-5 | high | 36 | 13739 | 755217 | 455s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-engineer | claude-opus-5-5 | high | 14 | 2328 | 171687 | 164s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-engineer | claude-opus-5-5 | high | 56 | 38827 | 3249598 | 618s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 14 | 2947 | 211432 | 247s | 1/1 omi-skill-simplify-review | FAIL d561067 |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 14 | 2166 | 196694 | 249s | 1/1 omi-skill-simplify-review | PASS 6682672 |
