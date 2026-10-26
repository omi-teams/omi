---
id: TASK-054
title: Store the Codex API key in the OS secret store
status: planned
depends: TASK-045
scope: src/omi/__init__.py, tests/**, README.md
role: omi-agent-engineer
skills: [omi-skill-windows-powershell]
workflow: omi-flow-feature-sensitive
step:
---
## Goal
`omi run --tool codex` gets `OPENAI_API_KEY` from Windows Credential Manager like the Claude token, with the env var as fallback.

## Acceptance criteria
- [ ] `omi token set --tool codex` stores the key under its own Credential Manager target; `omi token set` (claude) is unchanged.
- [ ] `omi run --tool codex` reads the stored key first, then `OPENAI_API_KEY`; the key still reaches the container by name only.
- [ ] The no-key error names the right command for each tool (today codex says `omi token set`).
- [ ] README documents it; `python tests/test_omi.py` passes.

## Checkpoint
Done:
Not done:
Tests:
Next:
