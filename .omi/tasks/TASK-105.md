---
id: TASK-105
title: CLI characterization test does not depend on what shares git's folder
status: in-progress
depends: TASK-104
plan: PLAN-003
scope: tests/test_omi.py
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-bugfix
step: reproduce
---
## Goal
CI on development is red since PR #100 (TASK-104), run 40663242734: `test_cli_characterization` (tests/test_omi.py:4004) sets PATH to git's folder and expects `tools: git ok, gh MISSING, docker MISSING` (line 4031). On the GitHub runner git lives in `/usr/bin`, next to gh and docker, so the line differs. The Linux worker and the Windows host keep git alone, which hid it. Test-only defect; src is fine.

## Acceptance criteria
- [ ] The test's PATH holds only git (and whatever git itself needs to run), independent of the machine: e.g. a temp folder with a link or shim to the real git, so gh, docker, claude and codex are always missing, also on ubuntu-latest where they share `/usr/bin`.
- [ ] No assertion in `test_cli_characterization` is removed or weakened; no src change.
- [ ] All tests pass on the Linux worker, on the Windows host, and in GitHub CI on the PR.

## Checkpoint
Done: test PATH is a temp folder with a symlink to git (Windows without symlink rights falls back to git's folder)
Not done: GitHub CI run on the PR
Tests: test_cli_characterization run alone passes on Linux; full `python3 tests/test_omi.py` was started but not seen to finish
Reproduce: GitHub CI run 40663242734 (ubuntu-latest, gh/docker in /usr/bin next to git) failed at tests/test_omi.py:4031; the worker and host keep git alone, so CI is the reproduction.
Host: python tests/test_omi.py (Windows) -> exit 0, ok
Next: review, then PR CI must be green before merge

## Steps
- plan started 2026-10-28 16:20
- plan done 2026-10-28 16:20
- reproduce started 2026-10-28 16:20

## Reports
2026-10-28 16:23 omi-agent-engineer (claude):
> The full `python3 tests/test_omi.py` run has now finished with exit code 0. The output ends with `ok`, so the whole suite passed on the Linux worker. That corrects my earlier "not seen to finish".
> 
> The Windows host and GitHub CI runs are still pending. The temp folder cleanup remains implicit, as noted before.
2026-10-28 16:25 hook post-run passed:
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
| omi-agent-engineer | claude-sonnet-5-5 | medium | 6 | 214 | 48664 | 159s | 1/1 omi-skill-lean-implementation | - |
