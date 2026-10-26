---
id: TASK-055
title: Pick Claude Code or Codex per role and task, switch on agent quota, resume after Coordinator quota
status: in-progress
depends: TASK-045, TASK-054
scope: src/omi/__init__.py, src/omi/template/**, .omi/agents/**, .omi/config.json, .omi/tasks/_template.md, .claude/skills/omi-task/**, AGENTS.md, tests/**, README.md
role: omi-agent-engineer
skills: [omi-skill-docker-worker-pitfalls, omi-skill-windows-powershell]
workflow: omi-flow-feature-sensitive
step: security
---
## Goal
The Coordinator can run any role with Claude Code or Codex, chosen in files; an agent that runs out of quota is continued by the other tool automatically; a new Coordinator session (Claude Code or Codex) resumes a task with nothing lost.

## Acceptance criteria
- [ ] Role files accept `tool: claude|codex` (default claude) and task frontmatter accepts `tool:` (overrides the role); `omi run --tool` overrides both. The chosen tool is shown in the run output and the `## Usage` row.
- [ ] Codex gets its own model aliases in config (e.g. `codex_models`), so a role's `model:`/`effort:` resolve correctly for either tool; an unknown alias fails clearly before any container starts.
- [ ] When the agent's CLI stops on a usage/quota limit (patterns per tool, tested against recorded sample output), `omi run` always reruns the same role once with the other tool in the same worktree, with a prompt note that a partial diff exists; the switch is recorded in `## Usage` and `## Checkpoint`. If the other tool also hits its limit or has no token, it stops with exit code 5 and a `QUOTA:` line, nothing discarded.
- [ ] `omi run` appends the agent's final report (verdict/DONE line and summary) to the task file in the worktree, so a Coordinator that dies mid-run loses nothing.
- [ ] `omi status` shows, for an in-progress task, its current step and a `resume: omi-task <ID>` line; AGENTS.md and the omi-task skill say how to resume from Codex or Claude Code.
- [ ] The default Claude path (no `tool:` anywhere) is unchanged; `python tests/test_omi.py` passes.

## Checkpoint
Done: tool selection (role/task/--tool), codex_models, quota switch + exit 5, ## Reports, status resume line, docs, tests.
Not done: nothing known.
Tests: python3 tests/test_omi.py ok.
Next: review.

Coordinator check round 1 FAIL:
1. `## Reports`: prefix every report line with `> ` (architect risk 2: a report with `
## `, `- [ ]` or `PO approval` lines must not create or hijack sections). Test with such a report.
2. Quota attempt rows: give them verdict `QUOTA->claude|codex` and exclude them from review-round counts in `prior_review` and `usage_totals` (architect risk 1). Test it.
3. `codex_effort`: the codex 0.164.0 binary does have `xhigh` (and `minimal`); map only `max` -> `xhigh`, pass the rest through.
4. No guessed Codex model IDs (`gpt-5`/`gpt-5-mini` are not in the 0.164.0 binary, which knows `gpt-5.6-*`, `gpt-6*`). Ship `codex_models` empty in both configs. For codex, a known Claude alias (`haiku|sonnet|opus`) with no `codex_models` entry means: omit `-m` so the Codex CLI uses its own default model, show `codex-default` in the run line and Usage. Full IDs matching the codex pattern pass through; an alias unknown to both maps still fails before any container starts. README: the PO fills `codex_models`.
Round 2: fixed all 4 (quoted ## Reports, QUOTA->tool verdict excluded from review counts, codex_effort max->xhigh, empty codex_models + codex-default). Tests: python3 tests/test_omi.py ok. Next: review.

Coordinator round 2 (from review PASS notes):
1. `quota_hit`: match only the CLI's own final error events, not the tail of all stdout: claude stream-json `{"type":"result", "is_error":true, ...}` result text; codex `--json` events of type `error` / `turn.failed` message. Test that a non-quota failure whose tool output contains "quota exceeded" does not switch.
2. Usage model cell names the tool for every codex row: `<model or codex-default> (codex)`; claude rows unchanged.
Known limit: quota patterns are not tested against real recorded limit output (cannot be captured without hitting a real limit); say so in README.
Round 3: quota_hit now reads only CLI error events; codex Usage cell always `<model> (codex)`; README known limit added. Tests: python3 tests/test_omi.py ok. Next: review.
## Steps
- plan started 2026-10-26 09:43
- plan done 2026-10-26 09:43
- architect started 2026-10-26 09:43
- architect done 2026-10-26 09:45
- build started 2026-10-26 09:45
- build done 2026-10-26 09:50
- review started 2026-10-26 09:50
- review done 2026-10-26 09:53
- security started 2026-10-26 09:53

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 14 | 7439 | 223795 | 91s | - | n/a |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 34 | 20208 | 959651 | 181s | 3/3 omi-skill-docker-worker-pitfalls omi-skill-windows-powershell omi-skill-lean-implementation | - |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 24 | 5539 | 417147 | 75s | 3/3 omi-skill-docker-worker-pitfalls omi-skill-windows-powershell omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 3796 | 96369 | 45s | - | PASS 14a739e |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 18 | 3988 | 225671 | 45s | 2/2 omi-skill-docker-worker-pitfalls omi-skill-windows-powershell | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 3931 | 100394 | 47s | - | PASS f9153bc |
| omi-agent-security-reviewer | claude-sonnet-5-5 | medium | 6 | 2356 | 103648 | 35s | 2/2 omi-skill-diff-security-review omi-skill-ci-workflow-audit | PASS 92628bf |
