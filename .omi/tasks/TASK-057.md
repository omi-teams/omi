---
id: TASK-057
title: Final evaluation of skills, roles and workflows against baselines
status: in-progress
depends: TASK-039
scope: docs/research/omi-eval.md, .omi/agents/**, .omi/skills/**, .omi/workflows/**, .omi/decisions.md
role: omi-agent-engineer
skills: []
workflow: omi-flow-spike
step: plan
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

## Checkpoint
Done:
Not done:
Tests:
Next:

## Steps
- plan started 2026-10-26 10:22
