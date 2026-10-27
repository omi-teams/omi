---
id: TASK-081
title: Spike - which Codex models and efforts this Codex session supports, and what each fits
status: in-progress
depends:
scope: docs/research/models-codex.md
role: omi-agent-researcher
skills: []
refs:
plan: PLAN-001
tool: codex
model: sonnet
effort: medium
workflow: omi-flow-spike
step:
---
## Goal
Codex runs often show `codex-default` / `none`, so nobody knows which model or effort ran. Find out, from inside the worker (Codex CLI 0.164.0, the PO's ChatGPT login), which Codex models and reasoning efforts are actually usable, and what kind of omi task each fits.

## Questions
1. Which model IDs does this `codex` CLI accept (`-m`) with the ChatGPT login? Look at what the CLI itself exposes (help, `~/.codex` model cache, error messages for an unknown model) and prove each with a one-line `codex exec -m <id> -c model_reasoning_effort=low "say ok"` run, or say why it was not run. Which model does `codex exec` use when no `-m` is given, and which effort?
2. Which `model_reasoning_effort` values exist (none, minimal, low, medium, high, xhigh?) per model, and what they change.
3. For each usable model x effort that matters, which omi work fits: mechanical, normal feature, bugfix, refactor, review, security review, architecture, research. Relative cost (ChatGPT plan limits) and speed from the run's usage numbers where possible.
4. A recommended `codex_models` mapping for the aliases haiku / sonnet / opus, and a default per omi role.

## Acceptance criteria
- [ ] Report saved at `docs/research/models-codex.md` (Vietnamese prose, English IDs): a table `model id | effort levels | fits | avoid for | relative cost/speed | evidence`, the default model/effort of `codex exec`, the proposed `codex_models` mapping and per-role defaults.
- [ ] Every claim says how it was verified (command run and its output, or CLI help/cache content); anything not verified is marked as such.

## Checkpoint
Done:
Not done:
Tests:
Next:
