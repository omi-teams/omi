---
id: TASK-139
title: Enforce the fix-round limit in code and force a re-plan on a repeated root cause
status: planned
depends: TASK-121, TASK-138, TASK-142
plan:
scope: src/omi/project/tasks.py, src/omi/project/workflows.py, src/omi/app/cli.py, src/omi/worker/run.py, src/omi/template/dot-omi/config.json, src/omi/template/dot-omi/agents/omi-agent-reviewer.md, src/omi/template/dot-omi/agents/omi-agent-security-reviewer.md, src/omi/template/dot-omi/workflows/**, src/omi/template/AGENTS.md, src/omi/template/dot-claude/skills/omi-task/SKILL.md, src/omi/template_shas.json, .omi/config.json, .omi/agents/**, .omi/workflows/**, AGENTS.md, .claude/skills/omi-task/SKILL.md, tests/test_tasks.py, tests/test_worker.py, tests/test_cli.py, tests/test_content.py, .omi/tasks/TASK-139.md
role: omi-agent-engineer
skills: []
refs: []
tool:
model:
effort:
step_settings:
workflow: omi-flow-feature-sensitive
step:
---
## Goal
A task can never run more than `max_fix_rounds` failed review rounds without a recorded PO decision, and when the failures share one root cause it goes back to its architect step instead of being patched again. Today both rules exist only as prose (AGENTS.md, omi-task skill, workflow "Review-fail rule"); TASK-120 ran 7 rounds because a standing "pick the recommended option" instruction skipped them.

## Acceptance criteria
- [ ] `max_fix_rounds` (default 2) in the template and repo `.omi/config.json`. A failed round is a review or security FAIL (the existing `tasks.prior_review` count, QUOTA rows excluded).
- [ ] When a task already has `max_fix_rounds` failed rounds, `omi step <ID> back` and `omi run <write role> <ID>` refuse with one `ROUND LIMIT: <ID> failed <N> review rounds; ask the PO` line and a non-zero exit, unless `--po "<PO's words>"` is given; that logs `PO round override <N+1>: <words>` under `## Steps` and allows exactly one more round. A standing instruction cannot pass the limit: the override needs the PO's words for this task and this round. Tested.
- [ ] Reviewer and security-reviewer reports end with `ROOT: same | new | n/a` (same = the findings are new instances of a root cause an earlier round already named). From round 2 on, a FAIL with `ROOT: same` makes `omi step back` move the task to its architect step (or the workflow's first write step before build) instead of build, and prints `REPLAN: same root cause`. Workflows without an architect step print the line and require `--po`. Tested with a fake report.
- [ ] The "Review-fail rule" in every template workflow, the omi-task skill and the AGENTS.md template describe the enforced behaviour (no prose-only limit left). Repo copies match; `template_shas.json` updated.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next: builds on `omi step <ID> back --to <step>` from TASK-138.
