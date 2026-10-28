---
id: TASK-096
title: Rename omi-squad2 to omi in code, skills and docs
status: in-progress
depends: TASK-093, TASK-094
plan: PLAN-003
scope: .claude/skills/omi-upgrade/SKILL.md, .omi/skills/delivery-ops/omi-skill-docker-worker-pitfalls/SKILL.md, .omi/skills/delivery-ops/omi-skill-incident/SKILL.md, .omi/skills/delivery-ops/omi-skill-release-checklist/SKILL.md, .omi/skills/delivery-ops/omi-skill-rollback/SKILL.md, .omi/skills/delivery-ops/omi-skill-windows-powershell/SKILL.md, README.md, src/omi/cli.py, src/omi/upgrade.py, src/omi/template/dot-claude/skills/omi-upgrade/SKILL.md, src/omi/template/dot-omi/skills/delivery-ops/omi-skill-docker-worker-pitfalls/SKILL.md, src/omi/template/dot-omi/skills/delivery-ops/omi-skill-incident/SKILL.md, src/omi/template/dot-omi/skills/delivery-ops/omi-skill-release-checklist/SKILL.md, src/omi/template/dot-omi/skills/delivery-ops/omi-skill-rollback/SKILL.md, src/omi/template/dot-omi/skills/delivery-ops/omi-skill-windows-powershell/SKILL.md, tests/test_omi.py, src/omi/template_shas.json, .omi/skills/CATALOG.md
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
The PO renamed the GitHub repo `omi-teams/omi-squad2` to `omi-teams/omi` (2026-10-28). Every default URL, install command and skill text points to the new name, so 0.3.2 installs from `omi-teams/omi`.

## Acceptance criteria
- [ ] `git grep omi-squad2` finds nothing outside `.omi/tasks`, `.omi/decisions.md`, `.omi/plans` and `docs/` (history stays as written).
- [ ] `OMI_REPO` default is `https://github.com/omi-teams/omi`; README install commands use it; local worktree paths in skill text use a placeholder (`<repo-name>`), not a hard-coded folder.
- [ ] Repo copies equal their template copies; catalogs regenerated; template shas updated if the tests require it. All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done: `omi-squad2` -> `omi` (URLs, OMI_REPO, container-name examples, tests) in every in-scope file; repo and template skill copies identical; `.omi/skills/CATALOG.md` regenerated (19 skills). No hard-coded worktree folder names found in skill text.
Not done: template_shas.json untouched (test suite did not require a change); not run on the Windows host.
Tests: `python3 tests/test_omi.py` exit 0 (Linux worker, full run).
Next: Coordinator review and commit; run the suite on the Windows host.

## Steps
- plan started 2026-10-28 16:36
- plan done 2026-10-28 16:36
- build started 2026-10-28 16:36

## Reports
2026-10-28 16:41 omi-agent-engineer (claude):
> DONE
> Files: README.md, src/omi/cli.py, src/omi/upgrade.py (`OMI_REPO` now `https://github.com/omi-teams/omi`), tests/test_omi.py, the 5 repo skill copies plus `.claude/skills/omi-upgrade/SKILL.md`, their 6 template copies (still identical), and `.omi/skills/CATALOG.md` (regenerated, 19 skills). Task checkpoint updated.
> Commit: `chore: rename omi-squad2 to omi in code, skills and docs`
> Tests: `python3 tests/test_omi.py` exit 0 on the Linux worker (full run). Not run on the Windows host.
> Open issues:
> - `src/omi/template_shas.json` untouched; the suite did not require a change.
> - The `.omi/tasks`, `decisions.md`, `plans` and `docs/` history still contain `omi-squad2` as intended, so the grep criterion holds for in-scope files.
> - Found no hard-coded worktree folder names in skill text, so no `<repo-name>` placeholder was needed.
2026-10-28 16:43 hook post-run passed:
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
| omi-agent-engineer | claude-haiku-5-5 | low | 14 | 3695 | 187706 | 249s | 1/1 omi-skill-lean-implementation | - |
