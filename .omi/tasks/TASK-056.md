---
id: TASK-056
title: Short readable container names; two TASK-055 review follow-ups
status: in-progress
depends: TASK-055
scope: src/omi/__init__.py, tests/**, README.md
role: omi-agent-engineer
skills: [omi-skill-docker-worker-pitfalls]
workflow: omi-flow-feature
step: build
---
## Goal
Agent containers are named `<TASK-ID>-<role short>-<tool>-<model>-<effort>-<HHMMSS>`, e.g. `TASK-055-reviewer-claude-sonnet-5.5-medium-143205`; plus two small fixes from the TASK-055 review.

## Acceptance criteria
- [ ] `container_name` drops the `omi-<repo>-` prefix and the `omi-agent-` role prefix, adds the tool, and keeps dots in the model version (`claude-sonnet-5-5` -> `claude-sonnet-5.5`, codex IDs as is, `codex-default` as is); Docker charset only. Proxy and network names follow it; `omi clean` still finds everything by label (repo stays in labels). `--prove` names its container the same way as a real run; the TASK-045 length test is updated to compare with a real-run name.
- [ ] Quota switch: when `--model` is a full ID for one tool, the other tool falls back to the role's alias (codex: `codex-default`) instead of exiting 5.
- [ ] `## Reports`: a report longer than the limit keeps its first and last lines (DONE/VERDICT and suggested commit), truncating the middle.
- [ ] `python tests/test_omi.py` passes.

## Checkpoint
Done: all 3 criteria + README + tests
Not done: -
Tests: python3 tests/test_omi.py ok
Next: review

## Steps
- plan started 2026-10-26 09:59
- plan done 2026-10-26 09:59
- build started 2026-10-26 09:59

## Reports
2026-10-26 10:00 omi-agent-engineer (claude):
> DONE
> - Files changed: `src/omi/__init__.py`, `tests/test_omi.py`, `README.md`, `.omi/tasks/TASK-056.md` (checkpoint).
> - Container names are now `<TASK>-<role short>-<tool>-<model>-<effort>-<HHMMSS>`, e.g. `TASK-055-reviewer-claude-sonnet-5.5-medium-143205`. The model version keeps its dot for Claude IDs, and the tool isn't repeated when the model already starts with it (`codex-default` gives `...-codex-default-...`). The `container_name` signature changed to `(role, tid, tool, model, effort, now)`. Proxy and network names are built from it. `--prove` uses the same naming, with the engineer role's tool and model.
> - Quota switch: if `--model` is a full ID for one tool, the other tool now uses the role's alias, and codex falls back to `codex-default`. A new test covers both cases.
> - `## Reports`: a new `clip_report` keeps the first and last lines of a report that exceeds 2000 characters and truncates the middle. A new test covers it.
> - Tests: `python3 tests/test_omi.py` passes. I updated the name assertions, and the length test in `test_egress` now pads the name past 63 characters, because the new real-run names are shorter than that.
> - Open issue: the quota-switch fallback has a leftover line that sets `models[other] = CODEX_DEFAULT` even when `other` is claude. That case returns the "cannot continue" stop right after, so the value is never used.
> 
> Suggested commit: `feat(omi): short readable container names, quota fallback to role alias, keep report head and tail`

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 28 | 7254 | 490938 | 75s | 2/2 omi-skill-docker-worker-pitfalls omi-skill-lean-implementation | - |
