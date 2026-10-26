---
id: TASK-077
title: CLI correctness - one test runner, hook results, step and scope messages
status: in-progress
depends: TASK-076
scope: src/omi/__init__.py, tests/**, src/omi/template/**, .claude/skills/omi-task/SKILL.md, .omi/tasks/_template.md
role: omi-agent-engineer
skills: [omi-skill-windows-powershell]
refs:
plan: PLAN-001
tool: claude
model: sonnet
effort: medium
workflow: omi-flow-feature
step: build
---
## Goal
Gaps #4 #6 #7 #8 #10 #11 #14 #21 (omi-board session 97bfceb1): small CLI behaviours that cost the Coordinator manual work.

## Acceptance criteria
- [ ] #6 The `test` command from `.omi/config.json` runs the same way on the host and in containers: through a shell (`sh -c` in containers; on the host `bash -c` when available, else `cmd /c` on Windows), so `VAR=1 cmd` works; a missing program prints `test command failed to start: <reason>` instead of a traceback. Tested.
- [ ] #14 `omi status` prints a hint when `test` is empty in `.omi/config.json`. Tested.
- [ ] #7 `omi hook <event> <ID>` records its result under `## Reports` like `omi run` does, so a passing manual `post-run` clears the step guard. Tested.
- [ ] #11 `omi run` of a write role exits non-zero when post-run failed even if the agent said DONE, and prints `post-run hook failed: the task cannot move to review`. Verify first whether 0.2.0 already returns 6; either way add a test.
- [ ] #8 `PO approval <step>:` is accepted with or without a leading `- `; the refusal message shows the exact line to add. Tested.
- [ ] #21 `omi run <role> <ID>` prints a warning when the task's current step has a different role (e.g. reviewer while step is `build`) and suggests `omi step <ID> done`/`next`. Tested.
- [ ] #4 When a `.git*` path is blocked as out of scope, the message says `.git* paths need an exact scope entry (no globs), e.g. .github/workflows/ci.yml`; `_template.md` (root and template) says the same in the scope comment. Tested.
- [ ] #10 Scope is read from one place: the task file on `development` (main checkout) for `omi run`, out-of-scope checks and the guard; the worktree copy's scope is ignored, and `omi-task` SKILL.md (root and template) says to edit scope only on development. Tested.
- [ ] `omi step <ID> done` on a `review` gate step refuses when the last verdict for that step's role in `## Usage` is FAIL (message says to run `omi step <ID> back`). Tested.
- [ ] `omi-task` SKILL.md (root and template): push `development` right after the start commit (with a remote), so the squash merge of the PR does not conflict with an unpushed local commit.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done: previous criteria remain implemented. Review round 1 fixes: configured shell test uses quoted sys.executable with forward slashes and runs with both Bash and cmd syntax; Windows shell selection filters System32 from PATH, uses the resolved Git Bash path, then falls back to cmd. Prompt formatting recognizes resolved bash.exe paths. Added mocked Windows regression coverage for Git Bash selection and cmd fallback, including System32-only PATH.
Not done: Windows host test run (unavailable in this Linux container).
Tests: python3 tests/test_omi.py passed on Linux (exit 0, ok), including the new Windows shell-selection tests.
Next: Coordinator runs python3 tests/test_omi.py on the Windows host, reviews the diff and commits on the host.

Review round 1 FAIL (reviewer not started; Coordinator findings from the Windows host run):
- tests/test_omi.py test_cli_correctness line 640 fails on Windows: the config test command calls `python3`, which on Windows is often the Microsoft Store stub, so the shell run returns non-zero and the temp dir stays locked (WinError 32). The test should build the command from sys.executable (forward slashes, quoted) so it runs on both hosts.
- test_command on Windows: shutil.which("bash") can return C:\Windows\System32ash.exe (the WSL launcher), which runs the command in a different Linux environment. On Windows the expected order is Git Bash, then cmd /c; a bash under System32 is skipped. Needs a test with a faked shutil.which.

## Steps
- plan started 2026-10-26 21:35
- plan done 2026-10-26 21:35
- build started 2026-10-26 21:35
- build done 2026-10-26 21:40
- review started 2026-10-26 21:40
- review failed 2026-10-26 21:41
- build started 2026-10-26 21:41

## Reports
2026-10-26 21:39 omi-agent-engineer (claude):
> DONE
> - Files changed: `src/omi/__init__.py`, `tests/test_omi.py`, `.claude/skills/omi-task/SKILL.md` and the template copy, `.omi/tasks/_template.md` and the template copy, and the `## Checkpoint` in `TASK-077.md`.
> - Commit message: `fix(cli): shell test command, hook results in Reports, step/scope/review-gate messages (TASK-077)`
> - Tests: `python3 tests/test_omi.py` prints `ok` on Linux. I did not run it on the Windows host, so that criterion is still open.
> - #11: 0.2.0 already returned 6 when post-run failed. I only added the `post-run hook failed: the task cannot move to review` message, and a test.
> - #6: when the config has a `test` command, the agent prompt's `Tests:` line shows the raw command, since containers run it with `sh -c`. The host runs it through `bash -c`, or `cmd /c` on Windows when bash is missing.
> - #10: scope is now read from `development` for `omi run` (rules and the out-of-scope check), the guard and the `.git*` hint. If the task isn't on `development`, scope is empty.
> - #14: the `omi status` hint prints only when `.omi/config.json` exists and `test` is empty.
> - Also added the SKILL.md instruction to push `development` after the start commit.
2026-10-26 21:39 hook post-run passed:
> Conflict. The container name "/tmp2n5p1ma1-TASK-001-engineer-codex-gpt-x-medium-143930" is already in useBind for 0.0.0.0:8080 failed: port is already in usewrote /tmp/tmptc4up1ej/.omi/skills/CATALOG.md (2 skills)
> create AGENTS.md
> create docker/Dockerfile
> create docker/prove.sh
> create docker/proxy.py
> create .claude/settings.json
> create .claude/skills/omi-idea/SKILL.md
> create .claude/skills/omi-release/SKILL.md
> create .claude/skills/omi-status/SKILL.md
> create .claude/skills/omi-task/SKILL.md
> create .omi/agents/CATALOG.md
> create .omi/agents/omi-agent-architect.md
> create .omi/agents/omi-agent-designer-ui.md
> create .omi/agents/omi-agent-devops.md
> create .omi/agents/omi-agent-docs-writer.md
> create .omi/agents/omi-agent-engineer.md
> create .omi/agents/omi-agent-qa-tester.md
> create .omi/agents/omi-agent-researcher.md
> create .omi/agents/omi-agent-reviewer.md
> create .omi/agents/omi-agent-security-reviewer.md
> create .omi/config.json
> create .omi/decisions.md
> create .omi/hooks/post-run.sh
> create .omi/plans/CATALOG.md
> create .omi/plans/PLAN-000.md
> create .omi/references/CATALOG.md
> create .omi/references/nextjs-app-router.md
> create .omi/references/postgres-conventions.md
> create .omi/rules/CATALOG.md
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
> [... truncated ...]
> ok
2026-10-26 21:43 omi-agent-engineer (codex):
> DONE
> Files changed: `src/omi/__init__.py`, `tests/test_omi.py`, `.omi/tasks/TASK-077.md`.
> Fixed Windows Bash selection and portable Python invocation; added regression coverage.
> Suggested commit: `fix(cli): skip WSL bash and use portable test interpreter`
> Tests: `python3 tests/test_omi.py` passed on Linux (`ok`).
> Checkpoint updated. Open issue: Windows host verification pending.
2026-10-26 21:43 hook post-run passed:
> Conflict. The container name "/tmpzbb000pp-TASK-001-engineer-codex-gpt-x-medium-144330" is already in useBind for 0.0.0.0:8080 failed: port is already in usewrote /tmp/tmpdtkg7_hp/.omi/skills/CATALOG.md (2 skills)
> create AGENTS.md
> create docker/Dockerfile
> create docker/prove.sh
> create docker/proxy.py
> create .claude/settings.json
> create .claude/skills/omi-idea/SKILL.md
> create .claude/skills/omi-release/SKILL.md
> create .claude/skills/omi-status/SKILL.md
> create .claude/skills/omi-task/SKILL.md
> create .omi/agents/CATALOG.md
> create .omi/agents/omi-agent-architect.md
> create .omi/agents/omi-agent-designer-ui.md
> create .omi/agents/omi-agent-devops.md
> create .omi/agents/omi-agent-docs-writer.md
> create .omi/agents/omi-agent-engineer.md
> create .omi/agents/omi-agent-qa-tester.md
> create .omi/agents/omi-agent-researcher.md
> create .omi/agents/omi-agent-reviewer.md
> create .omi/agents/omi-agent-security-reviewer.md
> create .omi/config.json
> create .omi/decisions.md
> create .omi/hooks/post-run.sh
> create .omi/plans/CATALOG.md
> create .omi/plans/PLAN-000.md
> create .omi/references/CATALOG.md
> create .omi/references/nextjs-app-router.md
> create .omi/references/postgres-conventions.md
> create .omi/rules/CATALOG.md
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
> [... truncated ...]
> ok

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 36 | 14114 | 886585 | 211s | 1/2 omi-skill-lean-implementation | - |
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 261855 | 3344 | 244608 | 144s | 2/2 omi-skill-windows-powershell omi-skill-lean-implementation | - |
