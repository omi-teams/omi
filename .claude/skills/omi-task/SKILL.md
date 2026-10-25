---
name: omi-task
description: Run one OMI task end to end - worktree, engineer, review, PR, CI, merge into development.
argument-hint: TASK-NNN
disable-model-invocation: true
---
Task: $ARGUMENTS. If empty, propose the `next` task from `python -m omi status` and wait for the PO.

The main checkout stays on `development`. `<wt>` is `../<repo-name>.wt/<ID>`.

1. Check that every `depends` task is done. Set `status: in-progress`, then commit on `development`.
2. If `<wt>` already exists, this is a resume: read its Checkpoint and verify it with `git -C <wt> status` and `git -C <wt> log development..HEAD`. Otherwise run `git worktree add <wt> -b task/<ID> development`.
3. Spawn `engineer` with `<wt>/.omi/tasks/<ID>.md` and `<wt>`. Pick the model by the AGENTS.md quota rules.
4. Handle the engineer's result:
   - `DONE`: spawn a fresh `reviewer` (skip it for docs-only or `.omi/`-only changes).
   - Review `FAIL`: give the findings to a new `engineer` run. After 2 failed fix rounds, ask the PO.
   - `NEEDS SCOPE`: if it fits the task goal, widen `scope` in the task file, commit, and rerun. Otherwise ask the PO.
5. On PASS, set `status: done` in `<wt>`'s task file and commit. Then:
   - With a GitHub remote: `git -C <wt> push -u origin task/<ID>`, `gh pr create --base development --head task/<ID> --fill`, then `gh pr checks --watch`. If CI fails, that counts as a fix round (step 4). When green, run `gh pr merge --squash --delete-branch`, then `git pull`.
   - Without a remote: `git merge --squash task/<ID>`, then commit `<type>: <title> (<ID>)`.
6. Post-merge check: run the project's test command on `development`. Then `git worktree remove <wt>` and `git branch -D task/<ID>`.
7. Report to the PO in at most 10 lines and stop. The PO picks the next task.
