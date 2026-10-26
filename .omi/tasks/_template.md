---
id: TASK-NNN
title: Short imperative title
status: planned
depends:
plan:  # Coordinator-owned optional id from .omi/plans/CATALOG.md
scope: src/feature/**, tests/test_feature.py
role: omi-agent-engineer  # a file in .omi/agents; its default skills count against the budget too
skills: []  # ids from .omi/skills/CATALOG.md; 6000 tokens per run, 2000 per skill; go to the write role only
refs: []  # Coordinator-owned ids from .omi/references/CATALOG.md; paths passed to all roles, outside budgets
tool:  # claude|codex; write role only; overrides its `tool:` (default claude); `omi run --tool` overrides both
model:  # Coordinator-owned: haiku|sonnet|opus or a full ID; overrides the role's, `omi run --model` overrides both
effort:  # Coordinator-owned: low|medium|high|max; same order
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
