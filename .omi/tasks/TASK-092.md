---
id: TASK-092
title: Bump omi to 0.3.1
status: done
depends: TASK-089, TASK-090, TASK-091
plan: PLAN-002
scope: pyproject.toml, README.md, tests/test_omi.py, .omi/version, src/omi/template_shas.json, AGENTS.md, src/omi/template/AGENTS.md, .omi/skills/workflow/omi-skill-task-brief/SKILL.md, src/omi/template/dot-omi/skills/workflow/omi-skill-task-brief/SKILL.md, .omi/skills/CATALOG.md
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: haiku
effort: low
step_settings:
workflow: omi-flow-feature
step: accept
---
## Goal
Release prep for PLAN-002: version 0.3.1 everywhere `omi --version` and the rc tag read it, as in TASK-088.

## Acceptance criteria
- [x] `omi --version` prints 0.3.1; `.omi/version` is 0.3.1; 0.3.1 template shas recorded (after the follow-up edits below, so they match).
- [x] TASK-091 follow-ups: `tokens:` in both omi-skill-task-brief copies equals the real count (`omi skills` catalog value); AGENTS.md (both copies) quota line reads "The Coordinator sets `model`/`effort` (and `tool`) per task in the task file at task start ...".
- [x] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Coordinator: Windows host suite passed (ok); skills --check ok; copies identical; 0.3.0 sha entry unchanged (no removed lines).
Done: version 0.3.1 in pyproject.toml, .omi/version, README (install tag + --version), tests/test_omi.py version assertion; template_shas.json 0.3.1 entry recorded after all edits (62 files, equals omi.template_shas()); TASK-091 follow-ups: tokens: 658 in both task-brief copies (matches CATALOG), AGENTS.md quota line "at task start" in both copies.
Not done: Windows host test run (Coordinator).
Tests: python3 tests/test_omi.py -> exit 0 (Linux worker); `python3 -m omi --version` -> omi 0.3.1.
Next: after merge: omi-release (rc), PO merges staging, then promote + tag v0.3.1; then `/omi-upgrade` in omi-board.

## Steps
- PO approval accept: Nghiệm thu, merge; ghi gap mới
- plan started 2026-10-28 11:19
- plan done 2026-10-28 11:19
- build started 2026-10-28 11:19
- build done 2026-10-28 11:27
- review started 2026-10-28 11:27
- review done 2026-10-28 13:03
- accept started 2026-10-28 13:03
- accept done 2026-10-28 13:03

## Reports
2026-10-28 11:24 omi-agent-engineer (claude):
> DONE
> 
> Files changed: pyproject.toml, .omi/version, README.md, tests/test_omi.py, src/omi/template_shas.json (0.3.1 entry appended), AGENTS.md, src/omi/template/AGENTS.md, both omi-skill-task-brief SKILL.md copies (tokens 580 → 658), .omi/skills/CATALOG.md (regenerated, no diff), .omi/tasks/TASK-092.md (checkpoint).
> Test: `python3 tests/test_omi.py` exit 0 on Linux; `PYTHONPATH=src python3 -m omi --version` prints omi 0.3.1. Windows host run not done (Coordinator).
> Commit message: `chore(release): bump omi to 0.3.1`
> Open issues: the 0.3.1 template shas were recorded after all edits and match `omi.template_shas()`. I did not re-check that the 0.3.0 entry is byte-identical, only that it is still present.
2026-10-28 11:26 hook post-run passed:
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
2026-10-28 11:31 omi-agent-reviewer (claude):
> ```
> VERDICT: PASS
> AC: `omi --version` prints 0.3.1; `.omi/version` is 0.3.1; 0.3.1 template shas recorded ✓ `python3 -m omi --version` printed "omi 0.3.1". The diff changes `.omi/version`, `pyproject.toml`, the README and the test assertion to 0.3.1. `template_shas.json["0.3.1"] == omi.template_shas()` returned True with 62 files. The 0.3.0 entry is untouched: the diff only appends and adds a comma after it.
> AC: TASK-091 follow-ups: `tokens:` equals the real count in both task-brief copies; AGENTS.md quota line says "at task start" ✓ Both SKILL.md copies read `tokens: 658`, and `.omi/skills/CATALOG.md` lists `[~658 tokens]`. `omi skills --check` printed "skills ok (19 checked)". The diff shows the "at task start" wording in both AGENTS.md copies, and `diff AGENTS.md src/omi/template/AGENTS.md` shows no difference. The `diff -r` of the two skills trees differs only in `CATALOG.md` and `authoring`, which exist only under `.omi/skills`, so the task-brief copies are identical.
> AC: All tests pass on the Linux worker and the Windows host UNVERIFIED Linux: `python3 tests/test_omi.py` exited 0 and ended with "ok". I could not run the Windows host suite. The only evidence is the Coordinator's line in the checkpoint, "Windows host suite passed (ok)", so I'm treating this criterion as unverified. Re-run it on Windows before merge if you want it confirmed.
> ```
> 
> I found no problems in the diff. The only file changed outside `scope` is `.omi/tasks/TASK-092.md`, the task's own checkpoint and report.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-haiku-5-5 | low | 26 | 5856 | 404816 | 286s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 8 | 1452 | 108954 | 199s | - | PASS f9379de |
