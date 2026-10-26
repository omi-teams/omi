---
id: TASK-062
title: Prove Codex end to end with a real key, including the quota switch
status: planned
depends: TASK-055, TASK-054
scope: docs/research/omi-eval.md, .omi/tasks/**, .omi/config.json
role: omi-agent-engineer
skills: []
workflow: omi-flow-spike
step:
---
## Goal
The biggest unproven part: `omi run --tool codex` with a real OpenAI key (stored by the PO with `omi token set --tool codex`), and the agent quota switch. Costs OpenAI API money; the PO stores the key and approves before any run.

## Acceptance criteria
- [ ] One small sandbox task run with `--tool codex` (codex-default model, or a `codex_models` entry the PO picks): DONE, tests pass, Usage row shows `(codex)`, key never in argv or logs.
- [ ] Quota switch exercised with a forced trigger (e.g. a sandbox-only fake limit event fed to `quota_hit`, or a real limit if one occurs); evidence recorded; the QUOTA patterns are updated if real output differs.
- [ ] Results in docs/research/omi-eval.md; what stays unproven is listed.

## Checkpoint
Done:
Not done:
Tests:
Next:
