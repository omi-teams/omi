---
id: TASK-116
title: Pilot omi board on real state
status: in-progress
depends: TASK-115
plan: PLAN-006
scope: docs/pilot-board.md, README.md
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
Prove the spec's success criteria 1-4 on the pilot omi-state and document how to use the board.

## Acceptance criteria
- [ ] `docs/pilot-board.md` (Vietnamese) lists criteria 1-4 with the command or action and its result on the pilot state (omi-pilot-splitbill, TASK-003), on the Windows host and Linux.
- [ ] README documents `omi board` in at most 8 lines.
- [ ] Gaps found are listed for a later plan.

## Checkpoint
Review round 1 FAIL: README.md - the "Bảng theo dõi (`omi board`)" section sits before "`omi init` tạo các file sau trong dự án:" and its table, so they fall under the board heading. Fix only: move the board section after the `omi init` table (keep its 7 lines). Change nothing else.
Host evidence (Coordinator, Windows 11 host, 2026-10-30, omi at development 478f894). The worker cannot read the real omi-state, so write the doc from these lines and do not re-run them:
- C1: `omi board` (port 8801) on the real `~/.omi/state` -> `/api/projects/omi-pilot-splitbill` returns plan PLAN-000 and kanban done=[TASK-003]. `/api/projects/omi-pilot-splitbill/tasks/TASK-003`: Steps and Reports text equal the file sections (compared byte for byte), and Usage has 2 rows, the same as the file (engineer + reviewer PASS 98f8665).
- C2: a copy of the state with `OMI_STATE=<copy>` (port 8802): editing TASK-003 `title:` -> the next API request returns the new title without restarting the server.
- C3: `title: <script>alert(1)</script>` comes back as plain JSON text, and the UI inserts text with textContent only (TASK-115 static test). The paths `/../../etc/passwd`, `/%2e%2e/%2e%2e/README.md`, `/api/projects/..%2f..%2f/tasks/x` and `/api/projects/omi-pilot-splitbill/tasks/..%2fTASK-003` (`curl --path-as-is`) all return 404. The CSP header is `default-src 'self'`.
- C4: Windows host: C1-C3 above, and `python tests/test_omi.py` -> ok (only the Playwright browser test is skipped). Linux: CI `ubuntu-latest` on development 478f894 -> success, and the Docker worker (Linux) runs `tests/test_omi.py` -> ok in every TASK-115/134 run. Browser QA in real Chrome at 360/390/768/1280 px is recorded in TASK-115.
- Gaps seen: no Playwright on the host or the worker (TASK-128); the board shows only the projects in the registry (the omi repo itself is not listed); a done task shows its last step as current, and Usage scrolls inside its card (TASK-125).
Done: docs/pilot-board.md (criteria 1-4, gaps) and README section "Bảng theo dõi" (6 lines).
Not done: nothing.
Tests: python3 tests/test_omi.py -> ok (Playwright browser test skipped).
Next: Coordinator review and commit.

## Steps
- plan started 2026-10-30 21:06
- plan done 2026-10-30 21:06
- build started 2026-10-30 21:06
- build done 2026-10-30 21:19
- review started 2026-10-30 21:19
- review failed 2026-10-30 21:26
- build started 2026-10-30 21:26

## Reports
2026-10-30 21:15 omi-agent-engineer (claude):
> DONE
> - Files: `docs/pilot-board.md` (new, Vietnamese), `README.md` (new "Bảng theo dõi (`omi board`)" section, 6 lines), `.omi/tasks/TASK-116.md` (checkpoint).
> - `docs/pilot-board.md` lists criteria 1–4 with the command, result and Windows/Linux evidence, plus the gaps for a later plan. It is copied from the Coordinator's checkpoint lines; I did not re-run any of them.
> - Commit: `docs(board): add omi board pilot results and README usage`
> - Tests: `python3 tests/test_omi.py` printed `ok`. The Playwright browser test was skipped because Playwright is missing.
> - Open issues: none. The README flags (`--port N`, `--no-open`, default port 8765) were checked against `src/omi/app/cli.py`.
2026-10-30 21:18 hook post-run passed:
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
2026-10-30 21:26 omi-agent-reviewer (claude):
> VERDICT: FAIL
> - README.md:110 The new "Bảng theo dõi (`omi board`)" section sits before "`omi init` tạo các file sau trong dự án:" and its table, so that content now falls under the board heading. -> Move the board section after the init table, or put the `omi init` lead-in under its own heading.
> 
> AC: `docs/pilot-board.md` (Vietnamese) lists criteria 1-4 with the command and result on the pilot state, on Windows and Linux. ✓ The file lists criteria 1-4 with commands and results. The Windows and Linux evidence matches the checkpoint lines. The doc says it was copied from the Coordinator's checkpoint, not re-run, which matches the task's instruction.
> AC: README documents `omi board` in at most 8 lines. ✗ The section is 5 lines, and the flags and default port 8765 match `src/omi/app/cli.py`. It sits in the wrong place and splits the `omi init` paragraph from its heading.
> AC: Gaps found are listed for a later plan. ✓ The "Gap cho plan sau" section lists all three gaps from the checkpoint.
> 
> `python3 tests/test_omi.py` printed `ok`. Two tests were skipped: the wheel test (pip missing) and the Playwright browser test. No finding depends on either.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 20 | 3172 | 238559 | 508s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 12 | 1601 | 158299 | 315s | - | FAIL 133e25d |
