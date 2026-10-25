---
id: TASK-051
title: Accept step refuses unticked acceptance criteria
status: planned
depends: TASK-038
scope: src/omi/__init__.py, tests/**, .claude/skills/omi-task/**, src/omi/template/dot-claude/skills/omi-task/**
role: omi-agent-engineer
skills: []  # step build adds omi-skill-lean-implementation
workflow: omi-flow-feature
step:
---
## Goal
A task cannot pass its `po` accept gate while an acceptance criterion is still `- [ ]`, and the Coordinator ticks the criteria the reviewer confirmed.

### Brief
- `step()` in `src/omi/__init__.py`: `done` (and `next` past) a `po`-gate step exits with the unticked lines listed when the task's `## Acceptance criteria` section still has a line starting `- [ ]`. Nothing changes otherwise.
- `.claude/skills/omi-task/SKILL.md` step 6 (root and template copy, identical, net growth at most 1 line): on PASS, tick (`- [x]`) each criterion the reviewer marked ✓ before the accept step.
- Tests: `python3 tests/test_omi.py`; a test with an unticked criterion refused at `done` on the po gate, and accepted once ticked.

## Acceptance criteria
- [ ] `omi step <ID> done` on a `po` gate is refused while `## Acceptance criteria` has `- [ ]` lines, listing them; allowed once all are `- [x]`.
- [ ] omi-task step 6 tells the Coordinator to tick reviewer-confirmed criteria; copies identical; at most 1 net added line.
- [ ] `python3 tests/test_omi.py` passes.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-042
