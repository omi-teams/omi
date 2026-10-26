---
id: TASK-066
title: Agents cannot change step or status in the task file
status: in-progress
depends: TASK-064
scope: src/omi/__init__.py, tests/**
role: omi-agent-engineer
skills: []
workflow: omi-flow-bugfix
step: review
---
## Goal
Bug: in TASK-064 the engineer wrote `step: done` into the task frontmatter, which broke `omi step` until the Coordinator restored it. `step:` and `status:` are Coordinator-owned (set by `omi step` and by the Coordinator).

## Acceptance criteria
- [ ] After an agent run, `omi run` compares the task file's `step`, `status`, `workflow`, `scope`, `role` and `skills` frontmatter with the values before the run; any change is reverted and reported as `REVERTED: <field>` (the rest of the file, e.g. Checkpoint, is kept).
- [ ] Test: an agent run that edits `step:` and the Checkpoint keeps the Checkpoint edit and restores `step:`.
- [ ] `python tests/test_omi.py` passes.

## Checkpoint
Done: revert_front + REVERTED output in run_role (src/omi/__init__.py); test in tests/test_omi.py
Not done: -
Tests: python3 tests/test_omi.py ok
Round 2: revert_front now restores raw original lines (same position, comments kept), restores lost/deleted frontmatter as `REVERTED: frontmatter`; unit test covers step/added/removed/lost/deleted. Tests ok.
Next: review/commit

Review round 1 FAIL:
1. tests/test_omi.py: no test edits `step:` (the reported bug). Add a direct `revert_front` unit test covering `step`, a field the agent added and one it removed.
2. src/omi/__init__.py revert_front: re-serialising via parse()/set_front drops `# comments` and reorders lines. Snapshot the raw original frontmatter lines of the owned keys and put those exact lines back (same position).
3. If the agent deletes the task file or removes the leading `---`, restore the original frontmatter (or the whole file from the snapshot) and print `REVERTED: frontmatter`.
## Steps
- plan started 2026-10-26 11:33
- plan done 2026-10-26 11:33
- reproduce started 2026-10-26 11:33
- reproduce done 2026-10-26 11:34
- fix started 2026-10-26 11:34
- fix skipped 2026-10-26 11:34: the reproduce run wrote the test and the fix together
- review started 2026-10-26 11:34
- review failed 2026-10-26 11:35
- fix started 2026-10-26 11:35
- fix done 2026-10-26 11:36
- review started 2026-10-26 11:36

## Reports
2026-10-26 11:34 omi-agent-engineer (claude):
> DONE
> - Files changed: `src/omi/__init__.py`, `tests/test_omi.py`, `.omi/tasks/TASK-066.md` (Checkpoint).
> - `omi run` now snapshots `step`, `status`, `workflow`, `scope`, `role` and `skills` before an agent run. For write roles it restores any that changed and prints `REVERTED: <field>`. Everything else in the file, such as the Checkpoint, is kept.
> - A field the agent added is removed, and a field it removed is put back.
> - Quota stops are covered too, because the check runs in `finally`.
> - Test: the mocked agent run edits `status:` and the Checkpoint. The Checkpoint edit stays, `status:` is restored, and `REVERTED: status` is printed. I used `status` rather than `step` because a `step:` in that test's fake worktree makes `run_role` load the workflow, which fails there on missing skills. The revert code treats every owned field the same way.
> - `python3 tests/test_omi.py` passes.
> - Suggested commit: `fix(run): revert agent edits to Coordinator-owned task frontmatter`
2026-10-26 11:35 omi-agent-reviewer (claude):
> VERDICT: FAIL
> - tests/test_omi.py:1537 The test edits `status:`, not `step:`. The criterion names `step:`, and the main bug was `step: done` breaking `omi step`. The engineer says a `step:` in the fake worktree makes `run_role` load the workflow, which then fails on missing skills. So the `step` path has no test. -> Add a test that edits `step:` plus the Checkpoint. It can be a separate case with a workflow and skills stubbed, or a direct `revert_front` unit test covering `step`, an added field and a removed field.
> - src/omi/__init__.py:62-78 `revert_front` rewrites the value from `parse()`, which drops `# comments`. `set_front` also moves the key to the end of the frontmatter, so a revert reorders fields and changes the original lines. -> Keep the raw original frontmatter lines in the snapshot and restore those, instead of re-serialising.
> - src/omi/__init__.py:1745 If the agent deletes the task file or removes the leading `---`, nothing is restored and no `REVERTED` is printed. The frontmatter is then lost without a report. -> Rewrite the original frontmatter, or the whole file, from the snapshot and report it as reverted.
> 
> AC: After an agent run, `omi run` reverts changes to the six fields and prints `REVERTED: <field>`, keeping the rest of the file ✓ `revert_front` plus the `finally` block in `run_role`. Covers changed, added and removed fields, and skips read roles. The test confirms this for `status`.
> AC: A test where an agent run edits `step:` and the Checkpoint ✗ The test edits `status:` instead. `step` is not exercised.
> AC: `python tests/test_omi.py` passes ✓ I ran it and it printed `ok`.
2026-10-26 11:36 omi-agent-engineer (claude):
> DONE
> - Files changed: `src/omi/__init__.py`, `tests/test_omi.py`, `.omi/tasks/TASK-066.md` (Checkpoint).
> - The run now snapshots the whole task file before the agent runs. `revert_front` puts the original raw lines of the six owned fields back at their original position, so `# comments` and order are kept. It prints `REVERTED: <field>` for each.
> - If the agent deletes the task file or removes the leading `---`, the original frontmatter or file is restored and `REVERTED: frontmatter` is printed.
> - New direct `revert_front` test covers an edited `step`, an added field, a removed field, lost frontmatter and a deleted file. The earlier run-level test (`status` plus Checkpoint) is unchanged.
> - Tests: `python3 tests/test_omi.py` prints `ok`.
> - Suggested commit: `fix(run): restore Coordinator-owned task frontmatter after agent runs`
> - Open issues: none. I didn't add a run-level test for `step:`, because a `step:` in that test's fake worktree makes `run_role` load the workflow, which fails there on missing skills. The direct test covers `step` instead.
2026-10-26 11:37 omi-agent-reviewer (claude):
> VERDICT: PASS
> - No blocking findings. Minor and not blocking: `src/omi/__init__.py:11` `front_of` finds the frontmatter by splitting on the first `---`, so a `---` inside a frontmatter value would cut it short. `parse` and `set_front` do the same, so this is consistent with the surrounding code.
> 
> AC: After an agent run, `omi run` reverts the six fields and prints `REVERTED: <field>`, keeping the rest of the file ✓ The `finally` block in `run_role` calls `revert_front`, which restores the original raw lines at their original position. `# comments` and field order are kept, and the Checkpoint edit is kept. Fields the agent added are removed, and fields it removed are put back. Read roles skip the revert. The test at tests/test_omi.py:1542 covers `status`.
> AC: A test where an agent run edits `step:` and the Checkpoint keeps the Checkpoint edit and restores `step:` ✓ The direct `revert_front` test at tests/test_omi.py:77-88 edits `step: done` and the Checkpoint. It asserts `step` is restored with its `# keep` comment, the Checkpoint edit stays, and the added and removed fields are handled. It is a unit test rather than a run-level one, which is the same `step` coverage round 1 asked for. The engineer explains that a run-level `step:` test fails in the fake worktree because `run_role` then tries to load the workflow and its skills.
> AC: `python tests/test_omi.py` passes ✓ I ran it and it printed `ok`.
> AC: Round-1 findings addressed ✓ The raw lines are restored, and lost frontmatter or a deleted file is restored and reported as `REVERTED: frontmatter`; the test covers both cases.
> AC: Changes stay within `scope` ✓ The diff touches only `src/omi/__init__.py` and `tests/test_omi.py`.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 28 | 4356 | 408440 | 57s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 8 | 1837 | 84559 | 32s | - | FAIL d614202 |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 18 | 3619 | 219439 | 47s | 1/1 omi-skill-debug-root-cause | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 1654 | 62362 | 28s | - | PASS ffd0ce6 |
