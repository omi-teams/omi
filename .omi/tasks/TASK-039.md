---
id: TASK-039
title: Carry-overs - skill fixes, test fix, review of unreviewed roles and commits
status: in-progress
depends: TASK-042, TASK-023, TASK-024, TASK-025, TASK-026, TASK-029, TASK-030, TASK-031
scope: .omi/agents/**, .omi/skills/**, src/omi/template/**, .claude/skills/**, tests/**
role: omi-agent-engineer
skills: []
workflow: omi-flow-feature
step: build
---
## Goal
Close the review carry-overs left by earlier tasks. The baseline evaluation moved to TASK-057 (PO, 2026-10-26).

## Acceptance criteria
- [ ] `omi-skill-data-review`: fix the contradiction ("stop at the first group with blocking findings, then continue" -> report blocking findings first, then continue), in `.omi/skills` and its template copy.
- [ ] `omi-skill-web-qa`: confirm the `npx playwright cli` fallback against the pinned upstream skill; fix or note the source.
- [ ] Audit (fresh instance, the reviewers were wrongly skipped, see decisions 2026-10-25) the 7 roles from TASK-029/030/031 and Coordinator commits 8bece61 (omi-task model-invocable), 94f3458 (omi-status pick-list), e7a1bfb (reviewer skip path rule): list findings in the Checkpoint and fix each real one in scope.
- [ ] `tests/test_omi.py` read-role Usage check: replace `not endswith("/1 |")` with an exact `-` cell assertion so a missing row fails.
- [ ] `python tests/test_omi.py` and `python -m omi skills --check` pass.

## Checkpoint
Done: data-review contradiction fixed (+template); test assertion now exact (`| - | n/a |`); audit below.
Audit findings: (1) qa-tester told to write evidence only to the prompt's temp path while omi-skill-web-qa says `qa/` in the worktree -> role now says use the temp path instead (fixed, both copies). (2) omi-task cites "AGENTS.md Quota rules" unquoted -> quoted heading (fixed, both copies). Other 5 roles and commits 8bece61/94f3458/e7a1bfb: no real findings; template copies identical.
Not done: web-qa `npx playwright cli` unverified - network blocked (raw.githubusercontent.com not in network_allow); `npx playwright cli` looks doubtful vs upstream `playwright-cli`; check at pinned b1a5903 and fix.
Tests: python3 tests/test_omi.py ok; PYTHONPATH=src python3 -m omi skills --check ok
Next: TASK-057
Coordinator: web-qa fallback confirmed against upstream b1a5903 `skills/playwright-cli/SKILL.md` lines 402-408 ("If global `playwright-cli` command is not available, try a local version via `npx playwright cli`" after `npx --no-install playwright --version`); the skill matches, no change. Temporary commits patch removed. The 7 roles: omi-agent-architect, -designer-ui, -researcher, -security-reviewer, -qa-tester, -devops, -docs-writer.

## Steps
- plan started 2026-10-26 10:16
- plan done 2026-10-26 10:16
- build started 2026-10-26 10:16

## Reports
2026-10-26 10:17 omi-agent-engineer (claude):
> BLOCKED on the `omi-skill-web-qa` criterion; the other four are done.
> 
> - **Not done:** I could not confirm the `npx playwright cli` fallback against the pinned upstream skill. `raw.githubusercontent.com` is not in `network_allow` (`.omi/config.json`), so the fetch returned 403. The command looks doubtful next to upstream's `playwright-cli`. I left the skill unchanged. Someone needs to check it at b1a5903 and fix it.
> - **Skill fix:** `omi-skill-data-review` now says "report blocking findings first, then continue with the remaining groups", in `.omi/skills` and the template copy.
> - **Test fix:** `tests/test_omi.py` now asserts the reviewer's Usage row ends with `| - | n/a |`, so a missing row fails.
> - **Audit findings (two, both fixed in both copies):**
>   - **QA evidence path:** `omi-agent-qa-tester` said to write evidence only to the prompt's temp path, while `omi-skill-web-qa` says `qa/` in the worktree. The role now says to use the temp path instead of `qa/`.
>   - **Quota rules wording:** `omi-task` cited "AGENTS.md Quota rules" unquoted. I quoted the heading.
> - **Rest of the audit:** the other five roles and commits 8bece61, 94f3458 and e7a1bfb had no real findings. The template copies match.
> - **Tests:** `python3 tests/test_omi.py` passes. `python -m omi skills --check` only runs with `PYTHONPATH=src` here; with it, it reports "skills ok (19 checked)".
> 
> Files changed:
> - `.omi/skills/data/omi-skill-data-review/SKILL.md` and its `src/omi/template/dot-omi/skills` copy
> - `.omi/agents/omi-agent-qa-tester.md` and its `src/omi/template/dot-omi/agents` copy
> - `.claude/skills/omi-task/SKILL.md` and its `src/omi/template/dot-claude/skills` copy
> - `tests/test_omi.py`
> - `.omi/tasks/TASK-039.md` (Checkpoint)
> 
> Suggested commit message: `fix: carry-over skill, role and test fixes from review audit`

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 22 | 4527 | 352245 | 56s | 1/1 omi-skill-lean-implementation | - |
