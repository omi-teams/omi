---
id: TASK-059
title: Slim omi-skill-debug-root-cause and omi-agent-security-reviewer, then re-measure
status: in-progress
depends: TASK-058
scope: AGENTS.md, .omi/skills/**, .omi/agents/**, src/omi/template/**, docs/research/omi-eval.md, tests/**
role: omi-agent-engineer
skills: []
workflow: omi-flow-feature
step: build
---
## Goal
Both cost more than a plain baseline with no correctness gain in TASK-057 (debug-root-cause +35% out/+29% cache; security-reviewer +44% out/+57% cache). Keep what they uniquely add, cut the rest, then re-run the same sandbox pairs.

## Acceptance criteria
- [ ] Each file is at most half its current token size, in `.omi` and the template copy; `python -m omi skills --check` and `python tests/test_omi.py` pass.
- [ ] Coordinator re-runs the TASK-057 bugfix and security pairs: the slimmed versions stay correct (planted issues caught, bug fixed); numbers appended to docs/research/omi-eval.md. (Original target "<= plain baseline +10% tokens" was not met: the extra cost is verification turns, not prompt size; PO kept the slim versions with verification, 2026-10-26.)

## Checkpoint
Round 2 done: debug-root-cause SKILL.md restored MIT comment (`<!-- Adapted from obra/superpowers systematic-debugging v6.3.0, MIT, Copyright (c) 2025 Jesse Vincent. -->`), now 294 tokens (<=295), .omi and template identical. Dropped the "Inputs" details and some wording to fit; `inputs` section kept (required by validator).
Round 2 done: added `- Diff touches auth, payment or secrets: \`opus\`, effort \`high\`.` under Quota rules in AGENTS.md and src/omi/template/AGENTS.md (identical).
Earlier: security-reviewer 453->225 tokens (.omi + template), unchanged this round.
Not done: Criterion 2 (sandbox re-run, docs/research/omi-eval.md) is the Coordinator's.
Tests: `PYTHONPATH=src python3 -m omi skills --check` ok (19 checked); `python3 tests/test_omi.py` ok.

Coordinator re-measure 2026-10-26 (fresh sandbox from this worktree's template, n=1, sonnet/medium; out / cache): bugfix + slim debug-root-cause 1192 / 106745, 18s, bug fixed; bugfix no skill 841 / 84563, 13s, bug fixed (+42% / +26%). Security slim role 722 / 50210, 12s, FAIL with injection + token leak + token to any host, verified by running, plus UNVERIFIED curl option injection via a `-` URL; plain read 697 / 32669, 11s, same three + scheme check (+4% / +54%). File size halved (591->294, 453->225 tokens) but per-run cost barely moved: the gap is the extra tool turns (running code to verify, grepping callers), each re-reading the context. PO decision: keep slim + verification.
Write (docs-writer): append a Vietnamese section "Đo lại sau TASK-059" to docs/research/omi-eval.md with the numbers above and the conclusion; change nothing else.
## Steps
- plan started 2026-10-26 10:41
- plan done 2026-10-26 10:41
- build started 2026-10-26 10:41

## Reports
2026-10-26 10:43 omi-agent-engineer (claude):
> DONE
> 
> Files changed (`.omi` copy and template copy of each, kept identical):
> - `.omi/skills/quality/omi-skill-debug-root-cause/SKILL.md`: 591 â†’ 289 tokens (target â‰¤295). Kept root cause before fix, grep all callers, regression test, and the `NEEDS SCOPE` escalation.
> - `.omi/agents/omi-agent-security-reviewer.md`: 453 â†’ 225 tokens (target â‰¤226). Kept location/why/verified per finding, no edits, output format, and injection handling.
> - `.omi/tasks/TASK-059.md`: checkpoint updated.
> 
> Suggested commit: `refactor(omi): slim debug-root-cause skill and security-reviewer agent`
> 
> Tests: `python -m omi skills --check` ok (19 checked; run with `PYTHONPATH=src`), `python tests/test_omi.py` ok.
> 
> Open issues:
> - Criterion 2 (sandbox re-run and numbers in `docs/research/omi-eval.md`) is the Coordinator's; I did not touch that file.
> - I dropped the "Use when / Do not use" routing lines from the security reviewer. The opus-for-auth/payment rule now lives only in AGENTS.md. Please confirm that is enough.
> - The debug skill's HTML attribution comment was removed; the `source_*` frontmatter fields still record the provenance.
2026-10-26 10:45 omi-agent-engineer (claude):
> DONE
> Files changed: `.omi/skills/quality/omi-skill-debug-root-cause/SKILL.md` and its template copy (identical); `AGENTS.md` and `src/omi/template/AGENTS.md` (identical, one bullet added under Quota rules); `.omi/tasks/TASK-059.md` (checkpoint).
> Commit: `fix(omi): restore debug skill attribution and add auth/payment quota rule`
> Tests: `PYTHONPATH=src python3 -m omi skills --check` ok (19 checked); `python3 tests/test_omi.py` ok.
> Debug skill is 294 tokens (limit 295) with the MIT comment restored. To fit, I dropped the Inputs detail to one line and tightened some wording; the `inputs` section stays because the validator requires it.
> Open: criterion 2 (sandbox re-run and numbers in `docs/research/omi-eval.md`) is still the Coordinator's.
> Note: `TASK-059.md` changed on disk while I was working; I left the external change as is.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-haiku-5-5 | low | 44 | 10895 | 611382 | 107s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-engineer | claude-haiku-5-5 | low | 30 | 9309 | 408870 | 103s | 1/1 omi-skill-lean-implementation | - |
