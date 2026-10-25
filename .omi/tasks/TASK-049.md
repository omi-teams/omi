---
id: TASK-049
title: Task skills go to write roles only
status: done
depends: TASK-048
scope: src/omi/__init__.py, tests/**, .omi/tasks/_template.md, src/omi/template/dot-omi/tasks/_template.md
role: omi-agent-engineer
skills: [omi-skill-lean-implementation]
---
## Goal
A read role (reviewer, security-reviewer, qa-tester, ...) does not get the task's `skills:`, which are meant for the implementer; it gets only its role defaults and the current step's skills. Saves reviewer tokens.

## Acceptance criteria
- [ ] `run_role`: the task's `skills:` are added only when the role has `access: write`; role defaults and matching step skills are added for every role.
- [ ] The budget check for a task (`omi skills check <task-file>`) is unchanged: it still counts the task role's defaults plus the task skills.
- [ ] The task template comment on `skills:` says they go to the write role only (root and template copy identical).
- [ ] Tests: a read role run on a task with `skills:` gets none of them (prompt and Usage `skills read` cell), a write role still does; `python tests/test_omi.py` passes.

## Checkpoint
Coordinator fix before review: the `Tests:` prompt line prints `python`, but the worker image has only `python3` (Dockerfile). Print `python3` for the host interpreter; update the test. Edit only `## Checkpoint` in this file.
Done: run_role adds task skills only for write roles; template comment (both copies); test. Tests pass.
Not done:
Tests: python3 tests/test_omi.py ok; Tests prompt line now prints python3.
Next: TASK-036

## Usage
| role | model | effort | input | output | cache | duration | skills read |
|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 26 | 3507 | 300248 | 172s | 1/1 omi-skill-lean-implementation |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 10 | 888 | 97291 | 26s | 1/1 omi-skill-lean-implementation |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 1213 | 63976 | 34s | 1/1 omi-skill-lean-implementation |
