---
id: TASK-073
title: Codex agents in the worker do not load the project AGENTS.md
status: planned
depends:
scope: src/omi/__init__.py, tests/**
role: omi-agent-engineer
skills: []
refs:
plan:
tool:
model: haiku
effort: low
workflow: omi-flow-feature
step:
---
## Goal
`AGENTS.md` at the repo root holds the Coordinator's instructions (talk to the PO in Vietnamese, never edit code). Codex reads it automatically from `/work`, so worker agents got Coordinator instructions on top of their role prompt (TASK-062/069: codex answered in Vietnamese). Make `codex_cmd` turn project docs off, e.g. `-c project_doc_max_bytes=0`, so a codex agent sees only its role prompt, like claude.

## Acceptance criteria
- [ ] `codex_cmd` passes the option that stops codex loading project docs (AGENTS.md); claude's command is unchanged. Tested on the argv.
- [ ] Real run (Coordinator, sandbox from `omi init` whose AGENTS.md says "Reply only in French"): `omi run --tool codex` engineer report is not in French and not in Vietnamese. Before the fix the same sandbox gives a French report.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:
