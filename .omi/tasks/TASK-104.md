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
Host check baseline FAIL (Coordinator, Windows): tests/test_omi.py:4034 test_cli_characterization: AssertionError (['skills'], 'wrote .omi\\skills\\CATALOG.md (18 skills)\n'); omi prints OS path separators. Make every path match in test_cli_characterization separator-agnostic (e.g. normalise `\\` to `/` in out/err before matching), not by changing src; check the other path assertions in that test the same way.
Host: python tests/test_omi.py (Windows, baseline round 2) -> exit 0, ok
Fix (baseline round 2): `cli()` in test_cli_characterization now replaces `\\` with `/` in stdout and stderr, so every path match in the test (CATALOG lines, `stamp  .omi/version`, guard/step/worker path endings, init/skip lines) is separator-agnostic. No src message prints a literal backslash (grep), so nothing else is masked. No src change. `python3 tests/test_omi.py` -> ok (exit 0) on Linux; Windows host re-check pending.
Done: baseline - suite green before any change; added `test_cli_characterization` (tests/test_omi.py, registered in `__main__`): runs `python -m omi` as a subprocess (PYTHONPATH=src, PATH = git's dir only, so gh/docker are absent on both OSes) and pins exit code + stdout/stderr of help/unknown/incomplete-arg fallthrough, version, init (twice), status (empty and with tasks), upgrade --apply/--to bogus, skills/rules/plans/references/agents/workflows (+ --check), skills check, github (+ --po), token set (usage; non-Windows message), hook, run, worker (+ --prove), guard (allow/block cases), parallel (all conflict kinds + ok), step (next/done/skip/back/bogus/invalid id/missing task). It uses no omi internals, so it should need no edits during the refactor. No src change.
Not done: refactor run 1 and run 2. Not pinned via CLI (need docker/network/a real worktree): `clean`, `upgrade --check` and real installs, `run`/`hook`/`worker` happy paths, `token set` on Windows, hidden `template-shas`; the existing in-process tests cover these.
Tests: `python3 tests/test_omi.py` -> ok (exit 0) on Linux, with the new test included; Windows host not run.
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

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 16 | 7738 | 242377 | 85s | - | n/a |
| omi-agent-engineer | claude-opus-5-5 | high | 36 | 13739 | 755217 | 455s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-engineer | claude-opus-5-5 | high | 14 | 2328 | 171687 | 164s | 1/1 omi-skill-lean-implementation | - |
