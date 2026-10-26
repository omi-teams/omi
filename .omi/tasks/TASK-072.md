---
id: TASK-072
title: Coordinator picks model and effort per task in the task file
status: in-progress
depends: TASK-071
scope: src/omi/__init__.py, tests/**, src/omi/template/**, .omi/tasks/_template.md, AGENTS.md
role: omi-agent-engineer
skills: []
tool:
workflow: omi-flow-feature
step:
---
## Goal
The Coordinator records its model choice in the task file (`model:` alias haiku|sonnet|opus or a full ID, `effort:`), so it survives resume and the quota switch; `omi run` resolves the alias for whichever tool runs. Order: `omi run --model/--effort` > task `model/effort` > role.

## Acceptance criteria
- [ ] `model:` and `effort:` in the task frontmatter override the role's; `--model/--effort` override both. Tested for claude and codex.
- [ ] An alias resolves through `models` for claude and `codex_models` for codex, also after a quota switch to the other tool; the container name and the Usage row show the resolved model, not the alias. Tested.
- [ ] A codex alias missing from `codex_models` still runs with `codex-default` and `omi run` prints one warning line naming the alias. Tested.
- [ ] `model` and `effort` are in `.omi/tasks/_template.md` (root and template) and are Coordinator-owned frontmatter (agents cannot change them).
- [ ] Template and root `AGENTS.md` say in one line that the Coordinator sets `model`/`effort` per task from the quota rules.
- [ ] A task's `tool:` (and `model`/`effort`) apply only to its write role (the implementer); read roles such as the reviewer keep their role's tool, so a codex-built task gets a claude review by default. `omi run --tool` still overrides. Tested.
- [ ] When an agent CLI exits non-zero for a reason other than a usage limit, `omi run` prints its error events (claude `result` is_error, codex `error`/`turn.failed`) and the exit code, and writes them to `## Reports`. Tested.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:
