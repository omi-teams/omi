---
id: TASK-064
title: Decode subprocess output as UTF-8 (Vietnamese mojibake on Windows)
status: in-progress
depends: TASK-060
scope: src/omi/__init__.py, tests/**
role: omi-agent-engineer
skills: []
workflow: omi-flow-bugfix
step:
---
## Goal
Bug: on Windows (locale cp1252) agent reports and other subprocess output are decoded with the locale, so UTF-8 text from containers and CLIs turns into mojibake (`â†’` for `→`, broken Vietnamese in `## Reports`). Root cause: `subprocess.run/Popen(..., text=True)` without `encoding`.

## Acceptance criteria
- [ ] Every `text=True` subprocess call in src/omi/__init__.py passes `encoding="utf-8"` (keep `errors="replace"` where present); a test fails if a `text=True` call without an encoding is added (scan the source).
- [ ] A test feeds UTF-8 bytes with `→` and Vietnamese through the agent run path and asserts they reach `## Reports` unchanged.
- [ ] `python tests/test_omi.py` passes on Windows and Linux.

## Checkpoint
Done:
Not done:
Tests:
Next:
