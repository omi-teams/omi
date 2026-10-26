---
id: TASK-NNN
title: Short imperative title
status: planned
depends:
scope: src/feature/**, tests/test_feature.py
role: omi-agent-engineer  # a file in .omi/agents; its default skills count against the budget too
skills: []  # ids from .omi/skills/CATALOG.md; 6000 tokens per run, 2000 per skill; go to the write role only
tool:  # claude|codex; overrides the role's `tool:` (default claude); `omi run --tool` overrides both
workflow: omi-flow-feature  # a file in .omi/workflows (see its CATALOG.md)
step:  # current step id; set only by `python -m omi step <TASK-ID> next|done|back|skip --why`
---
## Goal
One outcome, in one or two sentences.

## Acceptance criteria
- [ ] Testable criterion

## Checkpoint
Done:
Not done:
Tests:
Next:
