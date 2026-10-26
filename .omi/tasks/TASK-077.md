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
step:
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
Done:
Not done:
Tests:
Next:
