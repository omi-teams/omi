---
id: TASK-121
title: Coordinator proposes tool, model and effort; PO only approves
depends:
plan:
scope: src/omi/template/AGENTS.md, src/omi/template/dot-claude/skills/**, src/omi/template_shas.json, AGENTS.md, .claude/skills/**, tests/test_tools.py, .omi/tasks/TASK-121.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature
status: done
step: accept
---
## Goal
In every omi project, the Coordinator picks the fitting tool, model and effort for a task itself and presents it as one proposal for the PO to approve, with the other tool as the alternative; the PO no longer works out model or effort.

## Acceptance criteria
- [x] `## Task-start tool choice` in the template AGENTS.md (and the omi-task skill copy) says: the Coordinator decides tool, concrete model and effort from the quota rules and `## Models`, presents it first as "Approve: <tool> (<model>/<effort>) — <task-specific reason>", lists the other tool with its concrete model/effort as the alternative, and records the approved choice in the task; it no longer says "offer both tools and wait for the PO to choose".
- [x] When the PO names only a tool, the Coordinator chooses model and effort itself and states them, without another question; never `codex-default` or an omitted effort.
- [x] The repo's own `AGENTS.md` and `.claude/skills/omi-task/SKILL.md` match the template; `template_shas.json` is updated if the template hashes require it.
- [x] `tests/test_tools.py` checks the new wording instead of "PO chooses"; all tests pass.

## Checkpoint
Review round 1 PASS with a nit; PO: Accept + sửa nốt. Fix: `.claude/skills/omi-idea/SKILL.md:10` and `src/omi/template/dot-claude/skills/omi-idea/SKILL.md` still say "set only at task start from the PO's pick" -> "from the approved proposal or alternative"; update that template hash in `src/omi/template_shas.json`; extend the tests/test_tools.py check to the omi-idea copies. Nothing else.
Done: Fix round 1: changed both omi-idea copies from "PO's pick" to "approved proposal or alternative"; updated only that template hash; extended copy consistency and wording checks to omi-idea.
Not done: None for the requested fix.
Tests: Extended regression failed on the original omi-idea wording, then python3 tests/test_tools.py passed (exit 0) after the fix. python3 tests/test_omi.py passed (exit 0, final "ok"). Skipped: test_wheel_ships_web (pip missing); test_browser_layout_and_keyboard (Playwright missing; 360px/390px visual and keyboard checks unverified).
Next: Coordinator reviews the fix and commits on the host.
Session: codex 01a1906b-d90b-7c82-9971-540ac0bc3613

## Steps
- plan started 2026-10-31 12:25
- plan done 2026-10-31 12:25
- build started 2026-10-31 12:25
- build done 2026-10-31 12:38
- review started 2026-10-31 12:38
- review done 2026-10-31 12:49
- accept started 2026-10-31 12:49
PO approval accept: Accept + sửa nốt
- accept done 2026-10-31 12:50
- workflow reopened 2026-10-31 12:50: PO: Accept + sửa nốt (omi-idea still says PO's pick)
- review failed 2026-10-31 12:50
- accept failed 2026-10-31 12:50
- build started 2026-10-31 12:50
- build done 2026-10-31 13:03
- review started 2026-10-31 13:03
- review done 2026-10-31 13:18
- accept started 2026-10-31 13:18
PO approval accept: review passed thì merge và start task tiếp theo
- accept done 2026-10-31 13:18

## Reports
2026-10-31 12:32 omi-agent-engineer (codex):
> DONE
> Files: template/local AGENTS.md and omi-task/SKILL.md; src/omi/template_shas.json; tests/test_tools.py; .omi/tasks/TASK-121.md.
> Suggested commit: `fix(workflow): have coordinator propose tool model and effort`
> Tests: `python3 tests/test_tools.py` and `python3 tests/test_omi.py` passed.
> Skipped: web wheel test (pip missing); browser layout/keyboard checks (Playwright missing).
> Open issues: none. Checkpoint updated; no commit made.
2026-10-31 12:37 hook post-run passed:
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
2026-10-31 12:49 omi-agent-reviewer (claude):
> VERDICT: PASS
> - .claude/skills/omi-idea/SKILL.md:10 (and `src/omi/template/dot-claude/skills/omi-idea/SKILL.md`) The text still says "set only at task start from the PO's pick". This contradicts the new approve-a-proposal flow. AGENTS.md was fixed but this skill, which is in scope, was not. -> Change it to "from the approved proposal or alternative". Update the `template_shas.json` hash for the template copy.
> - `.omi/decisions.md:63` The 2026-10-26 entry still says "PO chooses". No new decision records this change. -> Add a decision entry. It sits outside the task's `scope`, so the Coordinator should do it.
> 
> AC: The `## Task-start tool choice` section in the template AGENTS.md and the omi-task skill copy has the Coordinator decide tool, model and effort, with "Approve: …" first, the alternative second, and the choice recorded in the task. The old "offer both tools and wait for the PO to choose" wording is gone. ✓ I read the diff, and the new tests assert these phrases and the absence of the old ones.
> AC: When the PO names only a tool, the Coordinator chooses model and effort itself and states both, without another question, and never uses `codex-default` or an omitted effort. ✓ The sentence is in all four copies and `test_task_start_tool_only` checks it.
> AC: The repo's `AGENTS.md` and omi-task skill match the template, and the `template_shas.json` hashes are updated. ✓ `sha256sum` shows the copies are identical, and the new hashes at lines 390 and 444 match them.
> AC: `tests/test_tools.py` checks the new wording instead of "PO chooses", and all tests pass. ✓ `test_tools.py` and `test_omi.py` both exit 0. `test_omi.py` skipped the playwright browser test, which is unrelated to this criterion.
2026-10-31 12:57 omi-agent-engineer (codex):
> DONE
> Files: both omi-idea/SKILL.md copies, src/omi/template_shas.json, tests/test_tools.py, .omi/tasks/TASK-121.md.
> Suggested commit: `fix(workflow): align idea skill with approved task proposals`
> Tests: regression failed before fix; test_tools.py and test_omi.py passed after fix.
> Skipped: web wheel test (pip missing); browser layout/keyboard checks (Playwright missing).
> Open issues: none for this fix. Checkpoint updated; no commit made.
2026-10-31 13:02 hook post-run passed:
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
2026-10-31 13:09 omi-agent-reviewer (claude):
> (no report)
> exit code 137
2026-10-31 13:17 omi-agent-reviewer (claude):
> VERDICT: PASS
> - No blocking problems. `tests/test_tools.py` and `tests/test_omi.py` both exit 0, and every changed file is inside the task `scope`.
> - `.omi/tasks/TASK-121.md` Usage table: the last reviewer row shows "exit code 137", so the earlier review run had no report. This is a process note only, not a code defect.
> 
> AC: Task-start section in the template `AGENTS.md` and the omi-task skill copy says the Coordinator decides tool, model and effort, shows "Approve: …" first and "Alternative: …" second, and records the approved choice in the task. "Offer both tools and wait for the PO to choose" is gone. ✓ I read it in the diff. `test_task_start_proposal` asserts the new phrases and the absence of "PO chooses", and `test_tools.py` passes.
> AC: When the PO names only a tool, the Coordinator picks model and effort itself and states both without another question. It never uses `codex-default` or an omitted effort. ✓ The sentence is in all four copies, `test_task_start_tool_only` checks it, and the test passes.
> AC: The repo's own `AGENTS.md` and omi-task skill match the template, and `template_shas.json` is updated. ✓ `sha256sum` shows the repo and template copies are byte-identical (AGENTS.md `b73de622…`, omi-task `0a8006fe…`, omi-idea `253a188d…`). The 0.5.0 entries at lines 387, 390 and 444 of `template_shas.json` match those hashes. Entries for older versions are unchanged. `grep` finds no remaining "PO's pick" or "PO chooses" in `AGENTS.md`, `.claude` or the template.
> [... truncated ...]
> AC (fix round: the omi-idea "PO's pick" wording) ✓ Both omi-idea copies now say "from the approved proposal or alternative". `test_task_start_copies_match` checks both copies and the `AGENTS.md` wording, and passes.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 1709470 | 6081 | 1622528 | 409s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 10 | 1639 | 145690 | 487s | - | PASS 47a01a6 |
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 3083795 | 9005 | 2973568 | 405s | 0/1 | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | n/a | n/a | n/a | 200s | - | n/a |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 12 | 1810 | 221272 | 358s | - | PASS 252ef33 |
