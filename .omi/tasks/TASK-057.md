---
id: TASK-057
title: Final evaluation of skills, roles and workflows against baselines
status: in-progress
depends: TASK-039
scope: docs/research/omi-eval.md, .omi/agents/**, .omi/skills/**, .omi/workflows/**, .omi/decisions.md
role: omi-agent-engineer
skills: []
workflow: omi-flow-spike
step: research
---
## Goal
One evaluation for everything, using real usage numbers. Keep only what earns its place. Estimated ~55 runs (2026-10-26); the PO picks full or lean scope before it starts.

## Acceptance criteria
- [ ] Every skill and every role is covered by a scenario inside the workflow runs below, each also run once with a plain prompt (no skill/role) as baseline; one baseline per skill or role, not per workflow.
- [ ] One scenario per workflow family (feature, bugfix, docs-only, change-request, incident, release), run in the Docker worker; record tokens, review rounds, steps skipped and problems.
- [ ] A skill, role or step that does not beat its baseline on correctness, tokens or review rounds is removed or reworked; decisions logged with the numbers.
- [ ] Report to the PO: total default context added by skills, roles and workflows.

## Plan (Coordinator, lean scope picked by the PO 2026-10-26)
Default context measured (tokens, `omi.tokens`): AGENTS.md 1297, skills CATALOG 889, workflows CATALOG 830, agents CATALOG 386 = 3402. Roles 239-632; skills 528-1107.
Sandbox: a toy Python repo made with `omi init` in the Coordinator scratchpad; every scenario is one sandbox task, same start commit. n=1 per variant (noisy; say so).
Scenarios (agent runs): feature (engineer+lean, reviewer), bugfix (engineer+debug-root-cause, reviewer), docs-only (docs-writer), change-request (architect+change-request), incident (devops+incident contain, engineer hotfix, reviewer), security (security-reviewer on a planted flaw). Release: Coordinator-only steps, tokens only.
Baselines (8): engineer plain role; engineer without lean-implementation; engineer without debug-root-cause; reviewer plain (planted bug); security-reviewer plain (planted flaw); docs-writer plain; architect plain; devops without incident skill.
Metrics: correctness (tests pass / planted issue found / criteria met), output and cache tokens, duration, review rounds.

## Results (Coordinator, sandbox runs 2026-10-26, n=1 each, claude-sonnet-5-5/medium unless noted; out = output tokens, cache = cache-read tokens, from each sandbox task's ## Usage)
| pair | variant | correct | out | cache | sec |
|---|---|---|---|---|---|
| feature: engineer + lean-implementation | full | yes (3/3 criteria) | 813 | 70714 | 13 |
| feature: engineer, no step skill | no skill | yes | 769 | 67358 | 13 |
| feature: plain role | plain | yes | 780 | 66638 | 13 |
| bugfix: engineer + debug-root-cause | full | yes (both pages right) | 1157 | 108690 | 16 |
| bugfix: engineer, no step skill | no skill | yes | 858 | 84531 | 14 |
| docs: docs-writer (haiku/low) | full | yes | 1422 | 90592 | 16 |
| docs: plain role (sonnet) | plain | yes | 953 | 65907 | 14 |
| change-request: architect (opus/high) + change-request | full | yes, 2 options + 1 recommended, found code already 0-based | 1645 | 52991 | 31 |
| change-request: plain read role | plain | invalid baseline (plain-read prompt is a review prompt; it reviewed instead) | 639 | 32581 | 9 |
| incident contain: devops + incident | full | yes, adds reproduction and "why the gate missed it" | 1859 | 92031 | 22 |
| incident contain: devops, no skill | no skill | yes | 1605 | 87463 | 19 |
| review planted off-by-one: reviewer | full | caught bug + missing test | 669 | 33518 | 11 |
| review planted off-by-one: plain read | plain | caught bug + missing test | 658 | 33078 | 9 |
| security planted shell=True + token leak: security-reviewer | full | caught injection + 2 leaks, verified by running | 830 | 51467 | 13 |
| security planted: plain read | plain | caught injection + leak + token sent to any host | 578 | 32812 | 10 |
Release workflow: Coordinator-only steps, no agent run; not measured.
Defects in omi found by the sandbox (fresh `omi init` project): (1) `omi init` writes no `.omi/skills/CATALOG.md`, so every task with a workflow fails until `omi skills` runs; (2) the default test command is `python -m pytest -q`, so read roles refuse to start in a project with plain test scripts and no pytest (needs `"test"` in config, undocumented in the template); (3) no `.gitignore` in the template, so `__pycache__` from the agent's own test run is reported OUT OF SCOPE (exit 3).
Fixture note: the planted review diffs also carried a host `.pyc` (Coordinator's fixture mistake); all reviewers flagged it as minor.

## Checkpoint
Done:
Not done:
Tests:
Next:

## Steps
- plan started 2026-10-26 10:22
- plan done 2026-10-26 10:23
- research started 2026-10-26 10:23
