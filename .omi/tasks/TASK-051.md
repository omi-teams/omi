---
id: TASK-051
title: Accept step refuses unticked acceptance criteria
status: in-progress
depends: TASK-038
scope: src/omi/__init__.py, tests/**, .claude/skills/omi-task/**, src/omi/template/dot-claude/skills/omi-task/**
role: omi-agent-engineer
skills: []  # step build adds omi-skill-lean-implementation
workflow: omi-flow-feature
step: build
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
- [ ] Carry-over from the TASK-041 review: omi-task step 5 FAIL writes the findings under a line `Review round <N> FAIL:` (the incremental review reads the files named after it); `prior_review` takes only path-like tokens (`dir/file`, or `name.ext` with a known extension, or `path:line`), not `e.g`, `1.5`, `v2.0`; `rev-parse` runs once.
- [ ] `python3 tests/test_omi.py` passes.

## Checkpoint
Done: all 4 criteria (step gate check, skill copies, prior_review/rev-parse/Review round FAIL line)
Not done: -
Tests: python3 tests/test_omi.py ok
Next: TASK-042

## Steps
- plan started 2026-10-25 22:47
- plan done 2026-10-25 22:47
- build started 2026-10-25 22:47

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 18 | 3690 | 252088 | 44s | 1/1 omi-skill-lean-implementation | - |
