---
id: TASK-068
title: Add rules auto-loaded by task scope, with their own token budget
status: in-progress
depends:
scope: src/omi/__init__.py, tests/**, src/omi/template/**, .omi/rules/**, .omi/config.json, AGENTS.md
role: omi-agent-engineer
skills: [omi-skill-windows-powershell]
tool:
workflow: omi-flow-feature
step:
---
## Goal
Rules in `.omi/rules/<id>.md` (frontmatter `id, summary, applies`) are added to an agent's prompt automatically when any `applies` glob matches the task `scope`, within a separate rule budget. Spec: `docs/specs/template-kinds.md` (Rules).

## Acceptance criteria
- [ ] `python -m omi rules` validates every rule (id = file name, summary, at least one `applies` glob, at most `rule_limits.rule_tokens`) and writes `.omi/rules/CATALOG.md`, one line per rule with its globs and token count.
- [ ] `rule_limits` in `.omi/config.json` overrides the defaults `{"tokens": 2000, "rule_tokens": 800}`; the skill budget is unchanged.
- [ ] `omi run` adds the paths of the matching rules to the prompt under a "Rules (you must follow these)" heading; a task with scope `src/**/*.go` gets rule `go` and not `python`. Tested.
- [ ] Over budget, `omi run` exits before starting the agent and names each rule and its token count. Tested.
- [ ] The template ships rules `go`, `python`, `postgres`, `nextjs`, `docker` (each at most 800 tokens) and its catalog; `omi init` into an empty directory creates them. Tested.
- [ ] Template and root `AGENTS.md` mention rules in one line each.
- [ ] All tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
