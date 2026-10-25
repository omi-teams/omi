---
id: TASK-041
title: Incremental review rounds (send only what changed)
status: planned
depends: TASK-040
scope: src/omi/__init__.py, .omi/agents/**, src/omi/template/**, tests/**
---
## Goal
After a failed review, the next round gets only the fixes and the previous findings, not the whole diff again, when that is safe.

## Acceptance criteria
- [ ] The first review reads the full diff. A later round gets the previous findings plus the diff since the last reviewed commit; a fresh reviewer instance is still used every round.
- [ ] If the follow-up diff touches files outside the previous findings, or the round is the third, the full diff is sent again.
- [ ] TASK-040 usage numbers show the saving on a test scenario, recorded in the checkpoint; if there is no saving the feature is reverted.
- [ ] `python tests/test_omi.py` passes.

- [ ] The review diff includes files the engineer added but did not stage (`git add -N`) or the docs state that the diff must be committed first.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-038
