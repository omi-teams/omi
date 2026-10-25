---
id: TASK-038
title: Wire workflows into omi-idea, omi-task and AGENTS.md
status: done
depends: TASK-048, TASK-040, TASK-033, TASK-034, TASK-035, TASK-036, TASK-037
scope: .claude/skills/**, src/omi/template/**, AGENTS.md, README.md, tests/**, src/omi/__init__.py, .omi/workflows/**, .omi/tasks/_template.md
role: omi-agent-engineer
skills: []  # step build adds omi-skill-lean-implementation
workflow: omi-flow-feature-sensitive  # changes the agent harness
step: accept
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
Architect (step architect): RECOMMEND A, the brief as written; Coordinator took A.
- `back` only when the current step has gate `review` and is started; target = nearest earlier step whose role is not coordinator and has `access: write`; log `- <cur> failed <stamp>` and `- <target> started <stamp>`; add `failed` to `STEP_LOG`.
- `verdict_of(report)`: last line matching `^\W*VERDICT:\W*(PASS|FAIL)`; Usage column `verdict`: `-` for write roles, `n/a` for a read role without a verdict; `record_usage` upgrades old headers (adds `skills read` and/or `verdict`); `usage_totals` accepts 7, 8 or 9 cells.
- feature-ui wording (workflow step tables are fixed): "a UI change in a sensitive area: run `omi-flow-feature-sensitive`; the Coordinator also runs `omi run omi-agent-designer-ui <ID>` before build and `omi run omi-agent-qa-tester <ID>` after security".
- Tests: back review->build then next reaches review; back from security in feature-sensitive -> build; back refused when not on a review gate, not started, or done; status shows `step:`; verdict PASS/FAIL/missing; 7/8-column tables upgrade.
Done: step back, verdict column, skills/AGENTS/feature-ui wording, catalog regenerated, tests.
Not done: -
Tests: python3 tests/test_omi.py ok
Next: review

## Steps
- plan started 2026-10-25 22:30
- plan done 2026-10-25 22:30
- architect started 2026-10-25 22:30
- architect done 2026-10-25 22:31
- build started 2026-10-25 22:31
- build done 2026-10-25 22:34
- review started 2026-10-25 22:34
- review done 2026-10-25 22:34
- security started 2026-10-25 22:34
- security done 2026-10-25 22:35
- accept started 2026-10-25 22:35
PO approval accept: Chấp nhận, merge (Recommended)
- accept done 2026-10-25 22:37

## Usage
| role | model | effort | input | output | cache | duration | skills read |
|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 12 | 6126 | 178448 | 74s | - |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 28 | 7919 | 544593 | 103s | 1/1 omi-skill-lean-implementation |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 1842 | 94782 | 32s | - |
| omi-agent-security-reviewer | claude-sonnet-5-5 | medium | 8 | 1436 | 144985 | 24s | 2/2 omi-skill-diff-security-review omi-skill-ci-workflow-audit |
