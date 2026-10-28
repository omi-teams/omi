---
id: TASK-091
title: Agent prompts: honest test claims, scope-first, real-data criteria, no tool preset at planning
status: planned
depends: 
plan: PLAN-002
scope: AGENTS.md, src/omi/template/AGENTS.md, .omi/agents/omi-agent-engineer.md, .omi/agents/omi-agent-reviewer.md, src/omi/template/dot-omi/agents/omi-agent-engineer.md, src/omi/template/dot-omi/agents/omi-agent-reviewer.md, .omi/skills/workflow/omi-skill-task-brief/SKILL.md, src/omi/template/dot-omi/skills/workflow/omi-skill-task-brief/SKILL.md, .claude/skills/omi-idea/SKILL.md, src/omi/template/dot-claude/skills/omi-idea/SKILL.md, .omi/agents/CATALOG.md, .omi/skills/CATALOG.md, src/omi/template_shas.json, tests/test_omi.py
role: omi-agent-engineer
skills: []
refs: []
tool:
model:
effort:
step_settings:
workflow: omi-flow-feature-sensitive
step:
---
## Goal
omi-board gaps #3, #9a, #11, #12a, #13: agents don't claim what they didn't run, don't stop early for scope, and criteria that read an existing format are checked on real data. Each edit is one or two lines; keep every prompt and skill inside its token budget (`omi skills --check`).

## Acceptance criteria
- [ ] Engineer prompt: finish everything inside `scope` first, then report `NEEDS SCOPE` once with all extra paths (#11); never write "tests passed" for a command that did not execute the tests (vet/lint/build only, or tests skipped): name what ran and what was skipped (#12a).
- [ ] Reviewer prompt: a criterion whose test was skipped or not executed is `UNVERIFIED`, never ✓, and the verdict cannot be PASS while one is (#9a); when a task parses an existing file format, check that fixtures match real files from the repo, not an idealised shape (#13).
- [ ] `omi-skill-task-brief`: add manifests (`go.mod`/`go.sum`, `package.json`/lockfile, `pyproject.toml`) to `scope` when the task may add a library (#11); a task that reads an existing format gets a criterion "runs on the real data in this repo" (#13).
- [ ] `omi-idea` step 5 and AGENTS.md: planning leaves `tool`, `model`, `effort` empty; they are set only at task start from the PO's pick (#3).
- [ ] Repo copies equal their template copies; catalogs regenerated; `omi skills --check` passes; template shas updated if the tests require it. All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next: independent of TASK-089/090; can run in parallel if the PO asks.
