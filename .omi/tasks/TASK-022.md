---
id: TASK-022
title: Skill standard, validator and authoring skill
status: in-progress
depends: TASK-021
scope: src/omi/__init__.py, src/omi/template/**, .omi/skills/authoring/**, tests/**
---
## Goal
Every omi-skill follows one contract and is checked by a command, so quality does not depend on the author.

## Acceptance criteria
- [ ] Contract (frontmatter + sections): id, group, when to use / not use, inputs, steps, outputs and evidence, stop/escalate conditions, tools needed, tokens, source (repo, commit/tag, file, license, use = reference|adapt|rewrite).
- [ ] `python -m omi skills --check` validates every skill: required parts present, size under the 2000-token cap, source recorded, no skill that widens permissions or scope.
- [ ] Skill `authoring/write-skill` (adapted from Anthropic skill-creator, Apache-2.0, notice kept) fits the 2000-token cap and covers: trigger wording, short body, references split out, and a baseline comparison before acceptance.
- [ ] Tests cover a valid skill and each failure; `python tests/test_omi.py` passes.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-023
