---
id: TASK-110
title: Document Windows PATH, test command and worker hosts for detached mode
status: in-progress
depends: TASK-108, TASK-109
plan: PLAN-005
scope: README.md, .omi/tasks/TASK-110.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: haiku
effort: low
step_settings:
workflow: omi-flow-feature
step: build
---
## Goal
Pilot gaps G1 and G7: README tells a new user what the pilot had to find out.

## Acceptance criteria
- [ ] README says how to put the Python `Scripts` dir on PATH on Windows (or use `python -m omi`), that an attached project needs `test` set in its state `.omi/config.json`, and that the worker adds the selected tool's API host (and chatgpt.com for a ChatGPT login) besides `network_allow`; it also documents the TASK-108 in-repo files warning and `omi step <ID> approve|reopen --why`; the `cli.py` usage line is left to TASK-111.
- [ ] At most 12 added lines, Vietnamese, matching README style.

## Checkpoint
Done: Replaced the fixed Windows Scripts path with the `sysconfig` discovery command; documented the attached project's test command in the state config location, including `OMI_STATE`; clarified the `--why` approve text is the PO's words. The existing three-line README addition stays within the 12 added line limit and leaves the cli.py usage line untouched.
Not done: None.
Tests: `python3 tests/test_omi.py` was run, but remained active beyond the execution window; no exit status or completion result was confirmed.
Next: Coordinator should confirm completion/result of `python3 tests/test_omi.py`.

## Steps
- plan started 2026-10-29 16:47
- plan done 2026-10-29 16:47
- build started 2026-10-29 16:47
- build done 2026-10-29 16:57
- review started 2026-10-29 16:57
- review failed 2026-10-29 17:03
- build started 2026-10-29 17:03

## Reports
2026-10-29 16:52 omi-agent-engineer (codex):
> DONE
> 
> - Files changed: [README.md](/work/README.md), [TASK-110.md](/work/.omi/tasks/TASK-110.md)
> - Added four Vietnamese lines covering the criteria; left the `cli.py` usage line unchanged.
> - Suggested commit: `docs: document detached mode setup and worker networking`
> - Tests: `python3 tests/test_omi.py` exited 0 and ended with `ok`.
> - Open issues: none.
2026-10-29 16:56 hook post-run passed:
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
2026-10-29 17:03 omi-agent-reviewer (codex):
> VERDICT: PASS
> AC: README documents Windows PATH/python invocation, attached-project test configuration, worker API hosts and network_allow, in-repo warning, and approve/reopen commands; cli.py unchanged ✓ README.md:26–32 and supplied diff; `python3 tests/test_omi.py` exited 0, ending `ok`.
> AC: At most 12 added README lines, Vietnamese, matching existing style ✓ Four added lines, including one blank; Vietnamese prose with inline commands.
2026-10-29 17:05 omi-agent-engineer (codex):
> BLOCKED | Updated [README.md](/work/README.md) with the corrected Windows Scripts lookup, state config location, and PO wording; updated [TASK-110.md](/work/.omi/tasks/TASK-110.md) checkpoint. The README addition stays within 12 lines; `cli.py` usage is unchanged. Suggested commit: `docs: clarify detached mode setup`. `python3 tests/test_omi.py` was started twice but neither run returned an exit status. Open issue: confirm test completion/result.
2026-10-29 17:08 hook post-run passed:
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
| omi-agent-engineer | gpt-6-luna (codex) | low | 1541816 | 3328 | 1501824 | 277s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | gpt-6.1-sol (codex) | medium | 721866 | 1876 | 666880 | 276s | - | PASS 22599c0 |
| omi-agent-engineer | gpt-6-luna (codex) | low | 164907 | 1628 | 138112 | 95s | 1/1 omi-skill-lean-implementation | - |
