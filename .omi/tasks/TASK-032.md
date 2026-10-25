---
id: TASK-032
title: Workflow engine (format, validator, step state, gates)
status: in-progress
depends: TASK-028
scope: src/omi/__init__.py, src/omi/template/**, .omi/workflows/**, .omi/tasks/_template.md, tests/**
---
## Goal
A workflow is a playbook file with a declared step table; omi tracks the current step in the task and enforces gates. The Coordinator still drives.

## Acceptance criteria
- [x] `.omi/workflows/<name>.md`: frontmatter lists steps (id, role, skills, input, output, gate: none|review|po, stop condition); body is the short playbook. Total at most 2000 tokens per workflow.
- [x] Task frontmatter gets `workflow:` (default `feature`) and `step:`; unknown workflow, role or skill fails; role and skill budgets from TASK-021/028 are checked per step.
- [x] `python -m omi step <TASK-ID> <next|done|skip --why>` records the step in the task file; it refuses to skip a gate step or jump over a step; a `po` gate refuses to continue until the Coordinator records the PO approval text in the task.
- [x] `python -m omi workflows` generates `.omi/workflows/CATALOG.md` (one line each) and `--check` validates all files.
- [x] Tests: step order, refused skip, po gate, unknown ids; `python tests/test_omi.py` passes.

- [x] `python -m omi workflows --check` exists and exits 0 on a valid folder: TASK-028 calls it before every read role when `.omi/workflows` exists, so a missing command would block all read roles.

## Checkpoint
Done: all AC. Workflow files `.omi/workflows/omi-flow-*.md` (frontmatter `id, summary, steps:` with one `- id: x | role: r | skills: a, b | input: .. | output: .. | gate: none|review|po | stop: ..` line per step; role `coordinator` = Coordinator's own step); `omi workflows [--check]` (check also fails a stale CATALOG.md); `omi step <TASK-ID> next|done|skip --why` writes `step:` and a `## Steps` log in the main-checkout task file; po gate needs a line `PO approval <step>: <PO's words>`; empty catalog + template copy; `_template.md` gets `workflow:`/`step:`.
Not done: default is `omi-flow-feature` (not bare `feature`, following the omi-agent-/omi-skill- prefixes); it does not exist until TASK-033, so `omi step` on a task without `workflow:` fails until then. `omi run` does not read the step yet (step skills are only budget-checked at `omi step next`).
Tests: python tests/test_omi.py -> ok (test_workflows)
Next: TASK-033

## Usage
| role | model | effort | input | output | cache | duration |
|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-opus-5-5 | high | 34 | 22439 | 754140 | 224s |
