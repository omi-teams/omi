---
id: TASK-038
title: Wire workflows into omi-idea, omi-task and AGENTS.md
status: in-progress
depends: TASK-048, TASK-040, TASK-033, TASK-034, TASK-035, TASK-036, TASK-037
scope: .claude/skills/**, src/omi/template/**, AGENTS.md, README.md, tests/**, src/omi/__init__.py, .omi/workflows/**
role: omi-agent-engineer
skills: []  # step build adds omi-skill-lean-implementation
workflow: omi-flow-feature-sensitive  # changes the agent harness
step:
---
## Goal
The Coordinator picks a workflow at planning time and follows it step by step; fix rounds return to the build step with its skills; review verdicts are on record.

### Brief
- `.claude/skills/omi-idea/SKILL.md` step 5 and `.claude/skills/omi-task/SKILL.md` step 1: pick the lightest fitting workflow from `.omi/workflows/CATALOG.md` and write `workflow:` (template field already exists in `.omi/tasks/_template.md`). omi-task step 5 FAIL: run `omi step <ID> back` before rerunning the engineer. Net growth at most 3 lines per skill; root and `src/omi/template/dot-claude/` copies identical.
- `AGENTS.md` (root and `src/omi/template/AGENTS.md`, identical): at most 4 added lines, naming `.omi/workflows/CATALOG.md` as the only workflow text loaded by default.
- `src/omi/__init__.py`: `step()` gets action `back`: allowed only while the current step is a `review`-gate step that is started (not done); moves `step:` to the nearest earlier step whose role is not `coordinator` and not a read role, logs `- <review> failed <stamp>` and `- <build> started <stamp>`; `next` from there reaches the review step again. Usage: `omi step <ID> next|done|back|skip --why`.
- `run_role`: parse `VERDICT: PASS|FAIL` from a read role's report and add it to the Usage row (new last column `verdict`, `-` for write roles); old 7/8-column tables keep parsing (same pattern as the `skills read` column in TASK-047).
- `.omi/workflows/omi-flow-feature-ui.md` "Use instead" (and template copy; regenerate the catalog): a UI change in a sensitive area runs `omi-flow-feature-sensitive` and the Coordinator inserts the `design` and `qa` steps.
- Pattern to copy: `step()` and `record_usage` in `src/omi/__init__.py`; tests next to `test_workflows` in `tests/test_omi.py`. Tests: `python3 tests/test_omi.py`.

## Acceptance criteria
- [ ] omi-idea / omi-task choose the lightest fitting workflow from the catalog and write `workflow:` into the task; (omi-task already drives `omi step`, TASK-048).
- [ ] AGENTS.md grows by at most 4 lines; the catalogs are the only workflow text loaded by default.
- [ ] Resume works: after an interruption `omi status` shows the task step and the Coordinator continues from it.
- [ ] Template and root copies identical; `python tests/test_omi.py` passes.

- [ ] Carry-over from the TASK-033 review: `omi-flow-feature-ui` "Use instead" for a UI change in a sensitive area has no actionable path; say the Coordinator runs `omi-flow-feature-sensitive` and inserts the `design` and `qa` steps.

- [ ] `omi step <ID> back` (or `next` from a FAILed `review` gate) returns to the previous write step, so a fix round runs with that step's skills; log it in `## Steps`.
- [ ] `omi run` saves the reviewer's `VERDICT: PASS|FAIL` in the Usage row (or `## Steps`), so the verdict is on record, not only in terminal output.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-041
