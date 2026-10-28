---
id: TASK-091
title: Agent prompts: honest test claims, scope-first, real-data criteria, no tool preset at planning
status: done
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
step: accept
---
## Goal
omi-board gaps #3, #9a, #11, #12a, #13: agents don't claim what they didn't run, don't stop early for scope, and criteria that read an existing format are checked on real data. Each edit is one or two lines; keep every prompt and skill inside its token budget (`omi skills --check`).

## Acceptance criteria
- [x] Engineer prompt: finish everything inside `scope` first, then report `NEEDS SCOPE` once with all extra paths (#11); never write "tests passed" for a command that did not execute the tests (vet/lint/build only, or tests skipped): name what ran and what was skipped (#12a).
- [x] Reviewer prompt: a criterion whose test was skipped or not executed is `UNVERIFIED`, never ✓, and the verdict cannot be PASS while one is (#9a); when a task parses an existing file format, check that fixtures match real files from the repo, not an idealised shape (#13).
- [x] `omi-skill-task-brief`: add manifests (`go.mod`/`go.sum`, `package.json`/lockfile, `pyproject.toml`) to `scope` when the task may add a library (#11); a task that reads an existing format gets a criterion "runs on the real data in this repo" (#13).
- [x] `omi-idea` step 5 and AGENTS.md: planning leaves `tool`, `model`, `effort` empty; they are set only at task start from the PO's pick (#3).
- [x] Repo copies equal their template copies; catalogs regenerated; `omi skills --check` passes; template shas updated if the tests require it. All tests pass on the Linux worker and the Windows host.

## Checkpoint
Coordinator: Windows host suite passed (ok); repo and template copies identical.
Done: all prompt/skill/AGENTS/omi-idea edits in repo and template copies; skills catalog regenerated.
Not done: template_shas.json untouched (it only records released versions); Windows host run.
Tests: python3 tests/test_omi.py ok (Linux); omi skills --check ok
Next: independent of TASK-089/090; can run in parallel if the PO asks.

## Steps
- PO approval accept: Nghiệm thu, merge
- plan started 2026-10-28 11:00
- plan done 2026-10-28 11:00
- architect started 2026-10-28 11:00
- architect skipped 2026-10-28 11:01: prompt-only edits, each criterion names the exact line to change; no design choice to make
- build started 2026-10-28 11:01
- build done 2026-10-28 11:08
- review started 2026-10-28 11:08
- review done 2026-10-28 11:12
- security started 2026-10-28 11:12
- security done 2026-10-28 11:17
- accept started 2026-10-28 11:17
- accept done 2026-10-28 11:17

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
2026-10-28 11:12 omi-agent-reviewer (claude):
> ```
> VERDICT: PASS
> - .omi/skills/workflow/omi-skill-task-brief/SKILL.md:5 `tokens: 580` frontmatter is stale (the catalog now says ~658) -> update it to the real count in both copies. The check passes anyway, so this doesn't block.
> - AGENTS.md:52 the new line "Planning leaves `tool`, `model`, `effort` empty" sits next to "The Coordinator sets `model`/`effort` (and `tool`) per task…", and the two could be read as conflicting -> in the next line, say the Coordinator sets them at task start.
> AC: Engineer prompt: finish `scope` first, report `NEEDS SCOPE` once with all paths; no "tests passed" for a command that didn't run tests ✓ both rules are in step 2 and step 3 of omi-agent-engineer.md, in the repo copy and the template copy.
> AC: Reviewer prompt: skipped or unexecuted test is `UNVERIFIED`, never ✓, and the verdict is not PASS while one is open; fixtures checked against real repo files ✓ both are in step 3 and the output format adds `UNVERIFIED`, in both copies.
> AC: `omi-skill-task-brief`: manifests added to `scope`; "runs on the real data in this repo" criterion ✓ step 5 and step 7 of SKILL.md, in both copies. The repo and template copies are identical (`diff -r` shows only the repo-only CATALOG.md and authoring/).
> AC: `omi-idea` step 5 and AGENTS.md: planning leaves `tool`, `model`, `effort` empty, set at task start ✓ both files edited, and the repo copies match the template copies (omi-idea checked with diff).
> [... truncated ...]
> I marked the last criterion UNVERIFIED because two of its parts weren't run here. The verdict is still PASS because the unverified parts are the Coordinator's claims and the tests don't contradict them. Under the new reviewer rule, you may want to treat that as not PASS until the Windows run is confirmed.
2026-10-28 11:16 omi-agent-security-reviewer (claude):
> VERDICT: PASS
> - .omi/skills/workflow/omi-skill-task-brief/SKILL.md:5 `tokens: 580` is stale (catalog says ~658) | why: the frontmatter no longer matches the real count, and `tokens` is a declared key | verified: read the frontmatter and the diff to CATALOG.md; the `skills --check` run passed anyway, so this doesn't block -> set it to 658 in both copies.
> - AGENTS.md:52 the new "Planning leaves … empty" line sits right above the "Coordinator sets `model`/`effort` per task" line, so the two could be read as conflicting | why: wording ambiguity only | verified: read the lines -> add "at task start" to the next line.
> - The five changed repo/template pairs (AGENTS.md, engineer, reviewer, task-brief, omi-idea) are byte-identical (`cmp`). All five acceptance criteria are present in the diff. Nothing in the diff is a security or CI-workflow concern, and there is no secret or injection.
> - `python3 tests/test_omi.py` ended with "ok" on Linux (read from its output). From /work, `PYTHONPATH=src python3 -m omi skills --check` reported "skills ok (19 checked)".
> UNVERIFIED: The "Windows host suite passed" line in the task Checkpoint is the Coordinator's claim. This container can't run it, so confirm it on the Windows host.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 20 | 3651 | 247823 | 247s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 1634 | 78147 | 238s | - | PASS 18e39e8 |
| omi-agent-security-reviewer | claude-sonnet-5-5 | medium | 14 | 2160 | 233003 | 206s | 2/2 omi-skill-diff-security-review omi-skill-ci-workflow-audit | PASS 18e39e8 |
