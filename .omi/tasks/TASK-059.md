---
id: TASK-059
title: Slim omi-skill-debug-root-cause and omi-agent-security-reviewer, then re-measure
status: in-progress
depends: TASK-058
scope: AGENTS.md, .omi/skills/**, .omi/agents/**, src/omi/template/**, docs/research/omi-eval.md, tests/**
role: omi-agent-engineer
skills: []
workflow: omi-flow-feature
step:
---
## Goal
Both cost more than a plain baseline with no correctness gain in TASK-057 (debug-root-cause +35% out/+29% cache; security-reviewer +44% out/+57% cache). Keep what they uniquely add, cut the rest, then re-run the same sandbox pairs.

## Acceptance criteria
- [ ] Each file is at most half its current token size, in `.omi` and the template copy; `python -m omi skills --check` and `python tests/test_omi.py` pass.
- [ ] Coordinator re-runs the TASK-057 bugfix and security pairs: the slimmed versions stay correct (planted issues caught, bug fixed) and use no more tokens than the plain baseline +10%; numbers appended to docs/research/omi-eval.md.

## Checkpoint
Done:
Not done:
Tests:
Next:
