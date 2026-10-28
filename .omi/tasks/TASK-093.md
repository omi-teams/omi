---
id: TASK-093
title: /omi-upgrade applies project files when they are behind the installed omi
status: in-progress
depends:
plan: PLAN-003
scope: .claude/skills/omi-upgrade/SKILL.md, src/omi/template/dot-claude/skills/omi-upgrade/SKILL.md, src/omi/__init__.py, tests/test_omi.py, src/omi/template_shas.json
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature
step: build
---
## Goal
omi-board had omi 0.3.1 installed but 0.3.0 project files, and `/omi-upgrade` stopped at `up to date`. After this, an upgrade always ends with `.omi/version` equal to the installed version.

## Acceptance criteria
- [ ] `/omi-upgrade` step 1 (both copies): when `upgrade --check` says `up to date` but `.omi/version` is older than the installed omi (or missing), run `python -m omi upgrade --apply` and continue with steps 4-5 instead of stopping; stop only when both are current.
- [ ] `omi status` hint for an older project stamp names the same command the skill runs (`python -m omi upgrade --apply`, or `omi init` if that is what actually stamps; pick the one that does, and the test proves it updates `.omi/version`). Tested.
- [ ] Repo copy equals its template copy; template shas updated if the tests require it. All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done: both skill copies (step 1 applies when stamp is older/missing), status hint now `python -m omi upgrade --apply`, tests (hint, apply stamps .omi/version, skill text)
Not done: Windows host run; template_shas.json untouched (0.3.1 is a released entry)
Tests: python3 tests/test_omi.py passed on Linux
Next: Coordinator review/commit

## Steps
- plan started 2026-10-28 13:27
- plan done 2026-10-28 13:27
- build started 2026-10-28 13:27

## Reports
2026-10-28 13:31 omi-agent-engineer (claude):
> DONE
> - Files changed: `.claude/skills/omi-upgrade/SKILL.md`, `src/omi/template/dot-claude/skills/omi-upgrade/SKILL.md` (identical), `src/omi/__init__.py`, `tests/test_omi.py`, `.omi/tasks/TASK-093.md`.
> - Skill step 1: when `upgrade --check` says `up to date`, it now compares `.omi/version` with `python -m omi version`. If the stamp is older or missing, it runs `python -m omi upgrade --apply` and continues with steps 4-5. It stops only when both are current.
> - `omi status` hint now says ``run `python -m omi upgrade --apply` ...``. Both `omi init` and `upgrade_apply` stamp `.omi/version`; I picked the one the skill runs. The test calls `upgrade_apply` and checks that `.omi/version` equals the installed version.
> - Tests: `python3 tests/test_omi.py` ran on Linux and printed `ok`. I did not run it on the Windows host.
> - `template_shas.json` is untouched. The 0.3.1 entry there is a released snapshot, and the tests didn't ask for an update.
> - Suggested commit: `fix(upgrade): apply project files when .omi/version is behind the installed omi`
2026-10-28 13:34 hook post-run passed:
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
| omi-agent-engineer | claude-sonnet-5-5 | medium | 16 | 3041 | 198334 | 249s | 1/1 omi-skill-lean-implementation | - |
