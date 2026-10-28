---
id: TASK-091
title: Agent prompts: honest test claims, scope-first, real-data criteria, no tool preset at planning
status: in-progress
depends: 
plan: PLAN-002
scope: AGENTS.md, src/omi/template/AGENTS.md, .omi/agents/omi-agent-engineer.md, .omi/agents/omi-agent-reviewer.md, src/omi/template/dot-omi/agents/omi-agent-engineer.md, src/omi/template/dot-omi/agents/omi-agent-reviewer.md, .omi/skills/workflow/omi-skill-task-brief/SKILL.md, src/omi/template/dot-omi/skills/workflow/omi-skill-task-brief/SKILL.md, .claude/skills/omi-idea/SKILL.md, src/omi/template/dot-claude/skills/omi-idea/SKILL.md, .omi/agents/CATALOG.md, .omi/skills/CATALOG.md, src/omi/template_shas.json, tests/test_omi.py
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature-sensitive
step: build
---
## Goal
omi-board gaps #3, #9a, #11, #12a, #13: agents don't claim what they didn't run, don't stop early for scope, and criteria that read an existing format are checked on real data. Each edit is one or two lines; keep every prompt and skill inside its token budget (`omi skills --check`).

## Acceptance criteria
- [ ] Engineer prompt: finish everything inside `scope` first, then report `NEEDS SCOPE` once with all extra paths (#11); never write "tests passed" for a command that did not execute the tests (vet/lint/build only, or tests skipped): name what ran and what was skipped (#12a).
- [ ] Reviewer prompt: a criterion whose test was skipped or not executed is `UNVERIFIED`, never ✓, and the verdict cannot be PASS while one is (#9a); when a task parses an existing file format, check that fixtures match real files from the repo, not an idealised shape (#13).
- [ ] `omi-skill-task-brief`: add manifests (`go.mod`/`go.sum`, `package.json`/lockfile, `pyproject.toml`) to `scope` when the task may add a library (#11); a task that reads an existing format gets a criterion "runs on the real data in this repo" (#13).
- [ ] `omi-idea` step 5 and AGENTS.md: planning leaves `tool`, `model`, `effort` empty; they are set only at task start from the PO's pick (#3).
- [ ] Repo copies equal their template copies; catalogs regenerated; `omi skills --check` passes; template shas updated if the tests require it. All tests pass on the Linux worker and the Windows host.

## Checkpoint
Coordinator: Windows host suite passed (ok); repo and template copies identical.
Done: all prompt/skill/AGENTS/omi-idea edits in repo and template copies; skills catalog regenerated.
Not done: template_shas.json untouched (it only records released versions); Windows host run.
Tests: python3 tests/test_omi.py ok (Linux); omi skills --check ok
Next: independent of TASK-089/090; can run in parallel if the PO asks.

## Steps
- plan started 2026-10-28 11:00
- plan done 2026-10-28 11:00
- architect started 2026-10-28 11:00
- architect skipped 2026-10-28 11:01: prompt-only edits, each criterion names the exact line to change; no design choice to make
- build started 2026-10-28 11:01

## Reports
2026-10-28 11:05 omi-agent-engineer (claude):
> DONE
> - Files changed: `AGENTS.md`, the engineer and reviewer prompts, the `omi-skill-task-brief` skill and the `omi-idea` skill, each in its repo copy and its template copy. Also `.omi/skills/CATALOG.md` (regenerated) and the task file's checkpoint.
> - The edits cover all five criteria. The engineer prompt now says to finish `scope` first, then report `NEEDS SCOPE` once, and not to write "tests passed" for a command that didn't run tests. The reviewer prompt adds `UNVERIFIED` for skipped tests, no PASS while one is open, and a check that fixtures match real repo files. The task-brief skill adds manifests to `scope` and the "runs on the real data in this repo" criterion. `AGENTS.md` and `omi-idea` step 5 say planning leaves `tool`, `model` and `effort` empty.
> - Commit message: `docs(agents): honest test claims, scope-first, real-data criteria, empty tool at planning`
> - Tests: `python3 tests/test_omi.py` passes on Linux, and `omi skills --check` passes (19 skills). I did not run on Windows.
> - Open issues:
>   - I left `src/omi/template_shas.json` unchanged. It only records released versions, and the tests didn't need it.
>   - `.omi/agents/CATALOG.md` is unchanged: I didn't touch the agent summaries.
>   - The `tokens: 580` frontmatter in the task-brief skill is stale; the catalog says ~658. The check still passes, so I left it.
2026-10-28 11:07 hook post-run passed:
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
| omi-agent-engineer | claude-sonnet-5-5 | medium | 20 | 3651 | 247823 | 247s | 1/1 omi-skill-lean-implementation | - |
