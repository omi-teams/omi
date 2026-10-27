---
id: TASK-080
title: Spike - which Claude models and efforts this Claude Code session supports, and what each fits
status: in-progress
depends:
scope: docs/research/models-claude.md
role: omi-agent-researcher
skills: []
refs:
plan: PLAN-001
tool: claude
model: sonnet
effort: medium
workflow: omi-flow-spike
step:
---
## Goal
The Coordinator must pick a concrete model and effort per task, never a default. Find out, from inside the worker (Claude Code CLI 2.1.302, the PO's session login), which Claude models and effort levels are actually usable, and what kind of omi task each fits.

## Questions
1. Which model IDs and aliases does this `claude` CLI accept (`--model`), and which ones actually answer with the session login? Prove each with a one-line `claude -p --model <id> --effort low "say ok"` run, or say why it was not run.
2. Which `--effort` levels exist (low, medium, high, xhigh, max?), and what do they change (thinking budget, speed, cost)?
3. For each usable model x effort that matters, which omi work fits: mechanical (rename, config, docs), normal feature, bugfix, refactor, review, security review, architecture, research. Note relative cost and speed (from the run's usage numbers where possible).
4. A recommended default per omi role (`.omi/agents`) and per workflow step type.

## Acceptance criteria
- [ ] Report saved at `docs/research/models-claude.md` (Vietnamese prose, English IDs): a table `model id | alias | effort levels | fits | avoid for | relative cost/speed | evidence`, plus the per-role defaults.
- [ ] Every claim says how it was verified (command run and its output, or CLI help text); anything not verified is marked as such.

## Checkpoint
Done:
Not done:
Tests:
Next:
