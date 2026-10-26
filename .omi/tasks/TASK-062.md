---
id: TASK-062
title: Prove Codex end to end with a real key, including the quota switch
status: in-progress
depends: TASK-055, TASK-065
scope: docs/research/omi-eval.md, .omi/tasks/**, .omi/config.json
role: omi-agent-engineer
skills: []
workflow: omi-flow-spike
step: research
---
## Goal
The biggest unproven part: `omi run --tool codex` with the PO's ChatGPT login (TASK-065; an API key also works but costs API money), and the agent quota switch.

## Acceptance criteria
- [ ] One small sandbox task run with `--tool codex` (codex-default model, or a `codex_models` entry the PO picks): DONE, tests pass, Usage row shows `(codex)`, key never in argv or logs.
- [ ] Quota switch exercised with a forced trigger (e.g. a sandbox-only fake limit event fed to `quota_hit`, or a real limit if one occurs); evidence recorded; the QUOTA patterns are updated if real output differs.
- [ ] Results in docs/research/omi-eval.md; what stays unproven is listed.

## Checkpoint
Done:
Not done:
Tests:
Next:

Coordinator results 2026-10-26 (fresh sandbox, development code after TASK-066, PO's ChatGPT login for codex, no API key):
- Real codex end to end: proven in TASK-065 (`omi run --tool codex`: DONE, tests pass, Usage `codex-default (codex) | medium | 115922 | 1040 | 110720 | 37s`).
- Quota switch, forced trigger: a wrapper replaced `omi.quota_hit` so every check of the claude attempt reports a limit stop; everything else was the real `omi run omi-agent-engineer TASK-001` path. Output: `tool: claude (claude-sonnet-5-5)`, then `QUOTA: claude hit its usage limit; rerunning omi-agent-engineer with codex (codex-default)`; codex continued on the partial diff ("kept the existing slugify, added tests"), DONE, tests pass, `slugify("Hello, World!") == "hello-world"`. Checkpoint line `QUOTA: claude hit its usage limit; omi-agent-engineer continued with codex on the partial diff.` Usage rows: `claude-sonnet-5-5 | medium | 8 | 635 | 67324 | 11s | - | QUOTA->codex` then `codex-default (codex) | medium | 99712 | 740 | 90496 | 29s | - | -`.
- Found: `quota_hit` is called twice per attempt (Usage tag and switch decision); a first forcing that fired only once tagged the row QUOTA->codex but did not switch. Harmless with the real (pure) function; noted.
- Still unproven: the real limit messages of claude 2.1.302 and codex 0.164.0 (QUOTA_PATTERNS untouched), the both-tools-out exit 5 in a real run (covered only by unit tests), an access token expiring mid-run. Codex answered in Vietnamese in the sandbox (it reads the sandbox AGENTS.md); harmless.
Write (docs-writer): append a Vietnamese section "Codex thật và chuyển tool khi hết quota (TASK-062)" to docs/research/omi-eval.md with these facts; change nothing else.
## Steps
- plan started 2026-10-26 11:38
- plan done 2026-10-26 11:38
- research started 2026-10-26 11:38
