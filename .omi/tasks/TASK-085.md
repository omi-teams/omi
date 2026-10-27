---
id: TASK-085
title: Per-step tool/model/effort in a task, and omi upgrade adds .gitattributes
status: in-progress
depends:
plan: PLAN-001
scope: src/omi/__init__.py, tests/test_omi.py, .omi/tasks/_template.md, src/omi/template/dot-omi/tasks/_template.md, AGENTS.md, src/omi/template/AGENTS.md, README.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: sonnet
effort: medium
workflow: omi-flow-feature
step:
---
## Goal
Close the open parts of gaps #9 and #19 (omi-board session 97bfceb1) before releasing 0.3.0. #9: TASK-083 lets the task's own role use the task's tool/model/effort, but other steps (architect, security) still need `--tool/--model/--effort` typed by hand. #19: `omi init` creates `.gitattributes`, but `omi upgrade --apply` does not, so existing projects never get it.

## Acceptance criteria
- [ ] A task can set `step_settings: <step>=<tool>/<model>/<effort>, ...` in its frontmatter (one line, e.g. `step_settings: architect=codex/opus/high, security=claude/opus/high`; any of the three parts may be empty, e.g. `review=claude//`). When `omi run <role> <ID>` runs the role of the task's current step and that step id is listed, those values are used. Precedence: `--tool/--model/--effort` > step_settings of the current step > task `tool/model/effort` (write role or the task's own role, as today) > role file > defaults. A malformed entry stops with a message showing the expected form. Tested, including a read role (architect, security-reviewer) and precedence.
- [ ] `omi upgrade --apply` creates `.gitattributes` with `* text=auto eol=lf` when missing and never overwrites an existing one (same rule as `omi init`, one shared helper). Tested.
- [ ] Both `_template.md` copies document `step_settings:` in one comment line; AGENTS.md (root and template) "Tool per run" sentence mentions it in the precedence order; README one line.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:
