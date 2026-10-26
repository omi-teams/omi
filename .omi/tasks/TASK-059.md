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
- [ ] Coordinator re-runs the TASK-057 bugfix and security pairs: the slimmed versions stay correct (planted issues caught, bug fixed) and use no more tokens than the plain baseline +10%; numbers appended to docs/research/omi-eval.md.

## Checkpoint
Done: debug-root-cause SKILL.md 591->289 tokens (.omi + template); omi-agent-security-reviewer.md 453->225 tokens (.omi + template). Both kept required sections, root cause before fix, grep callers, regression test; security location/why/verified, no edits.
Not done: Criterion 2 (sandbox re-run, docs/research/omi-eval.md) is the Coordinator's. Dropped the Use-when/Do-not-use routing lines from the security reviewer (model choice for auth/payment diffs now lives in AGENTS.md only; confirm that is enough).
Tests: `python -m omi skills --check` ok (19 checked); `python tests/test_omi.py` ok.
Next (done, was): targets (omi.tokens): debug-root-cause SKILL.md <= 295 (now 591), omi-agent-security-reviewer.md <= 226 (now 453). Keep: root cause before fix, grep all callers, regression test; security: location + why + how verified per finding, no edits. Criterion 2 (sandbox re-run) is the Coordinator's.

Coordinator round 2: (1) restore the MIT attribution in debug-root-cause as a short HTML comment with the copyright line (`Adapted from obra/superpowers systematic-debugging v6.3.0, MIT, Copyright (c) 2025 Jesse Vincent.`); the MIT license requires it. Stay <= 295 tokens by trimming elsewhere. (2) The dropped "opus when the diff touches auth, payment or secrets" rule is a Coordinator rule: add it as one bullet under `## Quota rules` in AGENTS.md and src/omi/template/AGENTS.md.
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

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-haiku-5-5 | low | 44 | 10895 | 611382 | 107s | 1/1 omi-skill-lean-implementation | - |
