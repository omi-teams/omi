---
id: TASK-056
title: Short readable container names; two TASK-055 review follow-ups
status: planned
depends: TASK-055
scope: src/omi/__init__.py, tests/**, README.md
role: omi-agent-engineer
skills: [omi-skill-docker-worker-pitfalls]
workflow: omi-flow-feature
step:
---
## Goal
Agent containers are named `<TASK-ID>-<role short>-<tool>-<model>-<effort>-<HHMMSS>`, e.g. `TASK-055-reviewer-claude-sonnet-5.5-medium-143205`; plus two small fixes from the TASK-055 review.

## Acceptance criteria
- [ ] `container_name` drops the `omi-<repo>-` prefix and the `omi-agent-` role prefix, adds the tool, and keeps dots in the model version (`claude-sonnet-5-5` -> `claude-sonnet-5.5`, codex IDs as is, `codex-default` as is); Docker charset only. Proxy and network names follow it; `omi clean` still finds everything by label (repo stays in labels). `--prove` names its container the same way as a real run; the TASK-045 length test is updated to compare with a real-run name.
- [ ] Quota switch: when `--model` is a full ID for one tool, the other tool falls back to the role's alias (codex: `codex-default`) instead of exiting 5.
- [ ] `## Reports`: a report longer than the limit keeps its first and last lines (DONE/VERDICT and suggested commit), truncating the middle.
- [ ] `python tests/test_omi.py` passes.

## Checkpoint
Done:
Not done:
Tests:
Next:
