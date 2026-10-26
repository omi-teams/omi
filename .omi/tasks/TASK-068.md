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
step: build
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
Done: all criteria (rules cmd, rule_limits, run prompt + budget stop, 5 template rules + catalog, AGENTS.md lines, test_rules).
Not done: -
Tests: python3 tests/test_omi.py ok
Next: review and commit.

## Steps
- plan started 2026-10-26 13:45
- plan done 2026-10-26 13:46
- build started 2026-10-26 13:46

## Reports
2026-10-26 13:48 omi-agent-engineer (claude):
> DONE
> - Files changed: `src/omi/__init__.py`, `tests/test_omi.py`, `AGENTS.md`, `src/omi/template/AGENTS.md`, `src/omi/template/dot-omi/rules/` (`go`, `python`, `postgres`, `nextjs`, `docker`, plus `CATALOG.md`), and the task's Checkpoint.
> - Commit: `feat(rules): auto-load rules by task scope with their own token budget`
> - Tests: `python3 tests/test_omi.py` passes, including a new `test_rules`.
>   - `test_rules` covers validation errors, `rule_limits` overrides, scope matching, and `omi init` into an empty directory.
>   - It also checks that `omi run` adds the rule paths under "Rules (you must follow these)", and that an over-budget run exits before any `docker run` and names each rule with its token count.
> - Open issues:
>   - A scope of `src/**/*.go` gets `go` and not `python`. The match runs the scope glob through `fnmatch` against each `applies` glob.
>   - `**/` at the start of an `applies` glob is optional, so `**/*.py` also matches `setup.py`.
>   - `omi run` only checks the rules that match the scope, so an invalid unrelated rule won't block it. `python -m omi rules` validates all of them.
>   - I did not add rules to the repo's own `.omi/`, only to the template.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 26 | 9725 | 519593 | 114s | 2/2 omi-skill-windows-powershell omi-skill-lean-implementation | - |
