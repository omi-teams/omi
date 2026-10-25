---
id: TASK-041
title: Incremental review rounds (send only what changed)
status: in-progress
depends: TASK-040
scope: src/omi/__init__.py, .omi/agents/**, src/omi/template/**, tests/**
role: omi-agent-engineer
skills: []  # step build adds omi-skill-lean-implementation
workflow: omi-flow-feature
step: build
---
## Goal
After a failed review, the next round gets only the fixes and the previous findings, not the whole diff again, when that is safe.

### Brief
- Code: `run_role` in `src/omi/__init__.py` (the `if read:` block that writes `/review/diff.patch`, ~line 1269) and `record_usage`.
- Record the reviewed commit: a read role's Usage `verdict` cell becomes `<PASS|FAIL> <sha7>` (`git rev-parse --short=7 HEAD` in the worktree); `usage_totals` and older rows keep parsing.
- Round N>1 (an earlier reviewer row has `FAIL <sha7>`) and N<3: write `diff.patch` = `git diff <sha7>` (fixes only) and add to the prompt "Incremental round: previous findings are under `## Checkpoint`; full diff at /review/full.patch only if needed". Previous-findings files = repo paths named in the Checkpoint lines after the last `Review round` heading. If the incremental diff touches any other file, or N>=3, send the full diff as today.
- Untracked files: include them in both diffs (`git add -N` on a temp index via `GIT_INDEX_FILE`, or `git diff` plus `git ls-files --others --exclude-standard` rendered as new-file patches); do not change the real index.
- Saving: a test builds a repo with a large first diff and a small fix, and asserts the incremental patch is smaller; print both sizes (tokens = bytes/4, as `tokens()`), and record them in the Checkpoint. The Coordinator records real Usage numbers on the next real FAIL round.
- TASK-040 fix: `parse_usage`/report with `usage` but no `result` prints the raw output, not `None`.
- Tests: `python3 tests/test_omi.py`; copy the git-repo setup used by existing `run_role` tests.

## Acceptance criteria
- [ ] The first review reads the full diff. A later round gets the previous findings plus the diff since the last reviewed commit; a fresh reviewer instance is still used every round.
- [ ] If the follow-up diff touches files outside the previous findings, or the round is the third, the full diff is sent again.
- [ ] TASK-040 usage numbers show the saving on a test scenario, recorded in the checkpoint; if there is no saving the feature is reverted.
- [ ] `python tests/test_omi.py` passes.

- [ ] The review diff includes files the engineer added but did not stage (`git add -N`) or the docs state that the diff must be committed first.

- [ ] Also fix from the TASK-040 review: when the harness JSON has `usage` but no `result`, `omi run` prints the raw output instead of `None`.

## Checkpoint
Done: verdict cell `<V> <sha7>`; `tree_diff` (untracked included, real index untouched); `prior_review`; incremental diff + full.patch + prompt note in `run_role` (round 2 only, files must be named after last `Review round`); raw-output print test for usage-without-result (code already printed raw output; now covered by a test).
Saving (test scenario, tokens = bytes/4): full 6296, incremental 56.
Not done: real Usage numbers (Coordinator, next real FAIL round). Docs not touched (diff includes unstaged files, so no commit-first note needed).
Tests: python3 tests/test_omi.py passes.
Next: TASK-042

## Steps
- plan started 2026-10-25 22:40
- plan done 2026-10-25 22:40
- build started 2026-10-25 22:40

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 24 | 9083 | 384220 | 101s | 1/1 omi-skill-lean-implementation | - |
