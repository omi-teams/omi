---
id: TASK-054
title: Store the Codex API key in the OS secret store
status: in-progress
depends: TASK-045
scope: src/omi/__init__.py, tests/**, README.md
role: omi-agent-engineer
skills: [omi-skill-windows-powershell]
workflow: omi-flow-feature-sensitive
step: architect
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

## Steps
- plan started 2026-10-26 09:27
- plan done 2026-10-26 09:27
- architect started 2026-10-26 09:27

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 12 | 2844 | 154398 | 46s | - | n/a |
