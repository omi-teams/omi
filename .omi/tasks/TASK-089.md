---
id: TASK-089
title: Clearer CLI feedback: Dockerfile diff hint, version check hint, hook result line
status: in-progress
depends: 
plan: PLAN-002
scope: src/omi/__init__.py, tests/test_omi.py
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
omi-board gaps #1, #2, #7, #8: when omi reports something, it says what happened and what to type next.

## Acceptance criteria
- [ ] When `docker/Dockerfile` differs from the template, `omi status` also prints one runnable command that shows the diff against the installed template file (e.g. `git diff --no-index <template path> docker/Dockerfile`) and says to merge by hand, since `omi init`/`upgrade` never overwrite it. Tested.
- [ ] `omi version` (and `--version`) prints the installed version plus a hint line `latest: python -m omi upgrade --check`; the `usage` text for `version` mentions it. Tested.
- [ ] `omi hook <event> <ID>` always prints a final line `hook <event> passed` or `hook <event> FAILED (exit N)`, also when the hook printed nothing. Tested.
- [ ] Regression test: `omi run` (write role) returns exit 6 when the post-run hook fails and the agent exited 0, and the engineer's `DONE` report does not change that. If the test shows the exit is already 6, no code change for this criterion.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Coordinator: Windows host suite passed (ok) on 6139e5e.
Review round 1 FAIL:
- tests/test_omi.py ~1500: make the agent mock return a `DONE` report in that `omi run` case, then assert `go() == 6`; keep the comment only if the test shows it.
- Also assert the `omi hook` FAILED path prints `hook post-run FAILED (exit 3)` as its last stdout line.
Done: all 4 code criteria; run exit was already 6 (regression assert added, no code change).
Not done: -
Tests: python3 tests/test_omi.py ok (Linux); Windows host ok (Coordinator, fix round 1).
Round 1 fixes done: agent mock returns DONE (exit 6 asserted); hook FAILED last-line asserted. Linux ok.
Next: Coordinator reviews, runs Windows host, commits.

## Steps
- plan started 2026-10-28 09:42
- plan done 2026-10-28 09:42
- build started 2026-10-28 09:42
- build done 2026-10-28 09:51
- review started 2026-10-28 09:51
- review failed 2026-10-28 09:56
- build started 2026-10-28 09:56

## Reports
2026-10-28 09:49 omi-agent-engineer (claude):
> DONE — all four code criteria are in place and `python3 tests/test_omi.py` passes on Linux. I didn't run the Windows host, so that last criterion is still open.
> 
> - **Files changed:** `src/omi/__init__.py`, `tests/test_omi.py`, and the checkpoint in `.omi/tasks/TASK-089.md`.
> - **Dockerfile hint:** when `docker/Dockerfile` differs from the template, `omi status` now also prints `git diff --no-index <template path> docker/Dockerfile` and says to merge by hand.
> - **Version:** `omi version` and `--version` add the line `latest: python -m omi upgrade --check`, and the usage text for `version` mentions it.
> - **Hook result line:** `hook_cmd` and `omi run` both print a final `hook <event> passed` or `hook <event> FAILED (exit N)` line. The change is in `hook_note`, so it holds when the hook printed nothing.
> - **Exit 6 regression:** the exit was already 6 when the post-run hook fails and the agent exited 0, so I made no code change there. I only added an assertion to the existing test. I didn't check how the agent mock reports `DONE`, so the test doesn't directly show that a `DONE` report leaves the exit at 6.
> - **Suggested commit:** `feat(cli): clearer feedback for Dockerfile diff, version check and hook result`
2026-10-28 09:51 hook post-run passed:
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
2026-10-28 09:56 omi-agent-reviewer (claude):
> VERDICT: FAIL
> - tests/test_omi.py:1500 The exit-6 regression test never shows the "`DONE` report does not change the exit" half of the criterion. The engineer's report admits they didn't check how the agent mock reports `DONE`. The new assert only checks that the stdout line `hook post-run FAILED (exit 3)` appears, which says nothing about `DONE`. -> Make the agent mock emit a `DONE` report, then assert `go() == 6`. Drop the misleading "despite DONE" comment unless that is shown.
> - .omi/tasks/TASK-089.md:21 The Windows host run is unverified, so the last criterion is open. The checkpoint says "Not done: Windows host run." -> Run `tests/test_omi.py` on the Windows host before passing.
> - src/omi/__init__.py:2461 In `omi run`, the `hook post-run FAILED` line isn't final. `hook_note` prints it, then "post-run hook failed: the task cannot move to review" follows. This is fine for `omi hook`, where `hook_note` is the last output, which is what the criterion requires. -> No change needed; this is only a note.
> 
> AC: Dockerfile diff hint in `omi status` ✓ `src/omi/__init__.py:1101` prints `git diff --no-index <template> docker/Dockerfile` and "merge by hand; omi init and upgrade never overwrite it". The test at `tests/test_omi.py:3750` asserts both.
> AC: `version`/`--version` prints the hint line and `usage` mentions it ✓ `src/omi/__init__.py:2538` prints `latest: python -m omi upgrade --check`, and the usage text for `version` now says "how to check for a newer one". The test at `tests/test_omi.py:82-83` asserts both.
> [... truncated ...]
> AC: All tests pass on Linux and Windows ✗ `python3 tests/test_omi.py` exits 0 on Linux (I ran it). The Windows host run was not done.
2026-10-28 10:02 omi-agent-engineer (claude):
> DONE: both review round 1 test fixes are in, and `python3 tests/test_omi.py` passes on Linux.
> - Files changed: `tests/test_omi.py` and the checkpoint in `.omi/tasks/TASK-089.md`. There are no code changes.
> - The `omi run` regression case now makes the agent mock report `DONE: all criteria met`, and it still asserts `go() == 6`. The "despite DONE" comment is removed.
> - The `omi hook` failure path now asserts that stdout ends with `hook post-run FAILED (exit 3)`.
> - Suggested commit: `test(cli): assert exit 6 with DONE report and hook FAILED last line`
> - Open: the Windows host run is still to do on the host.
2026-10-28 10:04 hook post-run passed:
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
| omi-agent-engineer | claude-sonnet-5-5 | medium | 24 | 3825 | 324092 | 397s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 1774 | 66509 | 239s | - | FAIL 6139e5e |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 20 | 2606 | 253908 | 347s | 1/1 omi-skill-lean-implementation | - |
