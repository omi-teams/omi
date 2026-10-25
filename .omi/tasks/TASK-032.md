---
id: TASK-032
title: Workflow engine (format, validator, step state, gates)
status: planned
depends: TASK-028
scope: src/omi/__init__.py, src/omi/template/**, .omi/workflows/**, .omi/tasks/_template.md, tests/**
---
## Goal
A workflow is a playbook file with a declared step table; omi tracks the current step in the task and enforces gates. The Coordinator still drives.

## Acceptance criteria
- [ ] `.omi/workflows/<name>.md`: frontmatter lists steps (id, role, skills, input, output, gate: none|review|po, stop condition); body is the short playbook. Total at most 2000 tokens per workflow.
- [ ] Task frontmatter gets `workflow:` (default `feature`) and `step:`; unknown workflow, role or skill fails; role and skill budgets from TASK-021/028 are checked per step.
- [ ] `python -m omi step <TASK-ID> <next|done|skip --why>` records the step in the task file; it refuses to skip a gate step or jump over a step; a `po` gate refuses to continue until the Coordinator records the PO approval text in the task.
- [ ] `python -m omi workflows` generates `.omi/workflows/CATALOG.md` (one line each) and `--check` validates all files.
- [ ] Tests: step order, refused skip, po gate, unknown ids; `python tests/test_omi.py` passes.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-033
