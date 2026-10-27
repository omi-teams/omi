---
id: TASK-080
title: Spike - which Claude models and efforts this Claude Code session supports, and what each fits
status: done
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
step: decide
---
## Goal
The Coordinator must pick a concrete model and effort per task, never a default. Find out, from inside the worker (Claude Code CLI 2.1.302, the PO's session login), which Claude models and effort levels are actually usable, and what kind of omi task each fits.

## Questions
1. Which model IDs and aliases does this `claude` CLI accept (`--model`), and which ones actually answer with the session login? Prove each with a one-line `claude -p --model <id> --effort low "say ok"` run, or say why it was not run.
2. Which `--effort` levels exist (low, medium, high, xhigh, max?), and what do they change (thinking budget, speed, cost)?
3. For each usable model x effort that matters, which omi work fits: mechanical (rename, config, docs), normal feature, bugfix, refactor, review, security review, architecture, research. Note relative cost and speed (from the run's usage numbers where possible).
4. A recommended default per omi role (`.omi/agents`) and per workflow step type.

## Acceptance criteria
- [x] Report saved at `docs/research/models-claude.md` (Vietnamese prose, English IDs): a table `model id | alias | effort levels | fits | avoid for | relative cost/speed | evidence`, plus the per-role defaults.
- [x] Every claim says how it was verified (command run and its output, or CLI help text); anything not verified is marked as such.

## Checkpoint
Done: research step (see Reports). In-container nested `claude -p` is "Not logged in"; PO approved the Coordinator probing on the host instead (2026-10-27).
Host evidence (Claude Code 2.1.302, PO session login, `claude -p --model <m> --effort low --output-format json "say ok"`; result | duration_ms | total_cost_usd | modelUsage):
- fable, claude-fable-5-1: is_error, "Fable 5.1 requires usage credits. Switch to another model" | ~630 | 0 | none
- opus: ok | 6493 | 0.1459 | claude-opus-5-5 ; claude-opus-5-5: ok | 1280 | 0.1281
- sonnet: ok | 5845 | 0.0727 | claude-sonnet-5-5 ; claude-sonnet-5-5: ok | 2354 | 0.0640
- haiku: ok | 1617 | 0.0039 | claude-haiku-5-5 ; claude-haiku-5-5: ok | 2224 | 0.0034
Effort probe (`claude -p --model haiku --effort <e> "What is 17*23? Answer with the number only."`; all answered 391): output_tokens low 29, medium 57, high 61, xhigh 67, max 207; cost ~0.0034-0.0036 each, duration 1.9-2.6 s. So all five levels are accepted; higher effort spends more output (thinking) tokens. Effect on hard tasks and on opus/sonnet: not measured.
Cost note: on a trivial prompt, opus is ~2x sonnet and ~35x haiku (mostly cached system-prompt cost).
Done: write step saved docs/research/models-claude.md in Vietnamese from Reports and host evidence above; role/workflow mappings are recommendations, not measured results. Commands and options checked against the task's recorded help/probes; role and step names checked against repo catalogs/workflows. No new model probes run.
Not done: independent host re-verification, Sonnet/Opus effort probes beyond low, and real-task quality/cost benchmarks; PO decision remains pending.
Tests: n/a (docs only)
Next: Coordinator reviews the documentation diff, then decide (PO gate).
## Steps
- plan started 2026-10-27 09:13
- plan done 2026-10-27 09:13
- research started 2026-10-27 09:13
- research done 2026-10-27 09:17
- write started 2026-10-27 09:17
- write done 2026-10-27 09:21
- decide started 2026-10-27 09:21

## Reports
2026-10-27 09:14 omi-agent-researcher (claude):
> ANSWER: Q1 (which models answer) and the usage numbers for Q3 can't be verified from this sandbox: the `claude` CLI returns "Not logged in" on every model. Only the CLI's `--model` and `--effort` help text could be checked. I also did not write `docs/research/models-claude.md`, because this researcher role has no writes.
> - CLI is 2.1.302. `--effort` accepts `low, medium, high, xhigh, max`. [`claude --help`, 2.1.302]
> - `--model` takes an alias (help text names `fable`, `opus`, `sonnet`) or a full model name. `haiku` is not in the help text. `--fallback-model` takes a comma-separated list. [`claude --help`, 2.1.302]
> - I ran `claude -p --model <m> --effort low --output-format json "say ok"` for `fable`, `opus`, `sonnet`, `haiku`, `claude-fable-5-1`, `claude-opus-5-5`, `claude-sonnet-5-5` and `claude-haiku-5-5`. Every run returned `is_error:true`, `result:"Not logged in · Please run /login"`, `terminal_reason:"api_error"`, zero tokens, zero cost and about 70 ms. No model was reached, so none is proven or disproven. [run in /tmp, 2026-10-27]
> - The model IDs `claude-fable-5-1`, `claude-opus-5-5`, `claude-sonnet-5-5` and `claude-haiku-5-5` come from this session's system prompt, not from a successful run. [system prompt]
> - `.omi/agents` has 9 role files: architect, designer-ui, devops, docs-writer, engineer, qa-tester, researcher, reviewer, security-reviewer. I did not read them, so I have not mapped any role to a default. [/work/.omi/agents]
> CONFIDENCE: high - on the flag list and the login failure, which are directly observed; the model-by-model findings are unknown, not low-confidence.
> [... truncated ...]
> NEEDS DECISION: Should the PO run `/login` in this container (or supply credentials) and re-run this task, and should a role with write access save the report to `docs/research/models-claude.md`?
2026-10-27 09:19 omi-agent-docs-writer (codex):
> DONE
> Files changed: docs/research/models-claude.md; .omi/tasks/TASK-080.md (checkpoint).
> Suggested commit: docs: document Claude model availability and effort recommendations
> Unverified: independent host results, Sonnet/Opus efforts beyond low, real-task quality and cost.
> Tests: not run (docs only).
> Open issues: Coordinator review and PO decision pending.
2026-10-27 09:21 hook post-run passed:
> Conflict. The container name "/tmpoix_xm8l-TASK-001-engineer-codex-gpt-x-medium-021922" is already in useBind for 0.0.0.0:8080 failed: port is already in usewrote /tmp/tmp5m9b9ipx/.omi/skills/CATALOG.md (2 skills)
> create AGENTS.md
> create docker/Dockerfile
> create docker/prove.sh
> create docker/proxy.py
> create .claude/settings.json
> create .claude/skills/omi-idea/SKILL.md
> create .claude/skills/omi-release/SKILL.md
> create .claude/skills/omi-status/SKILL.md
> create .claude/skills/omi-task/SKILL.md
> create .claude/skills/omi-upgrade/SKILL.md
> create .omi/agents/omi-agent-architect.md
> create .omi/agents/omi-agent-designer-ui.md
> create .omi/agents/omi-agent-devops.md
> create .omi/agents/omi-agent-docs-writer.md
> create .omi/agents/omi-agent-engineer.md
> create .omi/agents/omi-agent-qa-tester.md
> create .omi/agents/omi-agent-researcher.md
> create .omi/agents/omi-agent-reviewer.md
> create .omi/agents/omi-agent-security-reviewer.md
> create .omi/config.json
> create .omi/decisions.md
> create .omi/hooks/post-run.sh
> create .omi/plans/PLAN-000.md
> create .omi/references/nextjs-app-router.md
> create .omi/references/postgres-conventions.md
> create .omi/rules/docker.md
> create .omi/rules/go.md
> create .omi/rules/nextjs.md
> create .omi/rules/postgres.md
> create .omi/rules/python.md
> create .omi/skills/.gitkeep
> create .omi/skills/data/omi-skill-data-review/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-docker-worker-pitfalls/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-incident/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-release-checklist/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-rollback/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-windows-powershell/SKILL.md
> create .omi/skills/qa-web/omi-skill-web-qa/SKILL.md
> create .omi/skills/quality/omi-skill-ci-workflow-audit/SKILL.md
> create .omi/skills/quality/omi-skill-debug-root-cause/SKILL.md
> create .omi/skills/quality/omi-skill-diff-security-review/SKILL.md
> create .omi/skills/quality/omi-skill-simplify-review/SKILL.md
> [... truncated ...]
> ok

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-researcher | claude-sonnet-5-5 | medium | 10 | 1579 | 91664 | 40s | - | n/a |
| omi-agent-docs-writer | gpt-6.1-sol (codex) | low | 136643 | 3239 | 115712 | 111s | - | - |
PO approval decide: Adopt
