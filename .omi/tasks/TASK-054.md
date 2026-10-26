---
id: TASK-054
title: Store the Codex API key in the OS secret store
status: in-progress
depends: TASK-045
scope: src/omi/__init__.py, tests/**, README.md
role: omi-agent-engineer
skills: [omi-skill-windows-powershell]
workflow: omi-flow-feature-sensitive
step: review
---
## Goal
`omi run --tool codex` gets `OPENAI_API_KEY` from Windows Credential Manager like the Claude token, with the env var as fallback.

## Acceptance criteria
- [ ] `omi token set --tool codex` stores the key under its own Credential Manager target; `omi token set` (claude) is unchanged.
- [ ] `omi run --tool codex` reads the stored key first, then `OPENAI_API_KEY`; the key still reaches the container by name only.
- [ ] The no-key error names the right command for each tool (today codex says `omi token set`).
- [ ] README documents it; `python tests/test_omi.py` passes.

## Checkpoint
Done: all 4 criteria (token set --tool codex, token(tool), run_role, README, tests)
Not done: -
Tests: python3 tests/test_omi.py ok
Next: review

## Steps
- plan started 2026-10-26 09:27
- plan done 2026-10-26 09:27
- architect started 2026-10-26 09:27
- architect done 2026-10-26 09:30
- build started 2026-10-26 09:30
- build done 2026-10-26 09:31
- review started 2026-10-26 09:31

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 12 | 2844 | 154398 | 46s | - | n/a |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 24 | 4500 | 345280 | 53s | 2/2 omi-skill-windows-powershell omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 8 | 1226 | 89369 | 23s | - | PASS 7e829d6 |
