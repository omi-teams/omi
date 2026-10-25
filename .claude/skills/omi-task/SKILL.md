---
name: omi-task
description: Run one OMI task end to end - worktree, engineer in the Docker worker, review, PR, CI, merge into development.
argument-hint: TASK-NNN
---
Task: $ARGUMENTS. If empty, propose the `next` task from `python -m omi status` and wait for the PO.

The main checkout stays on `development`. `<wt>` is `../<repo-name>.wt/<ID>`.

1. Check that every `depends` task is done and that the task's `role` (a file in `.omi/agents`) and `skills` (chosen from `.omi/skills/CATALOG.md`, regenerate with `python -m omi skills`) pass `python -m omi skills check <task-file>` (role default skills count too). Set `status: in-progress`, then commit on `development`.
2. If `<wt>` already exists, this is a resume: read its Checkpoint and verify it with `git -C <wt> status` and `git -C <wt> log development..HEAD`. Otherwise run `git worktree add <wt> -b task/<ID> development`.
3. Run the engineer in the Docker worker (never spawn an `omi-agent-engineer` subagent, never run it on the host):
   `python -m omi run <role> <ID> [--model M --effort E]` (role from the task, default `omi-agent-engineer`; add `--tool codex` to use Codex). Pass `--model/--effort` only when the AGENTS.md quota rules differ from `.omi/agents/<role>.md`. It prints the engineer's report.
   If it stops because Docker is not running or no token is found, tell the PO (token: `python -m omi token set`) and stop. There is no host fallback.
4. Check the diff before committing: `git -C <wt> status` and `git -C <wt> diff`. `omi run` prints `OUT OF SCOPE: <path>` (exit 3) for changes outside `scope`. Refuse those, and always refuse changes to `.gitattributes`, `.gitmodules` or any `.git*` path unless the scope names it: `git -C <wt> checkout -- <path>` or delete the new file. Then `git -C <wt> add -A` and commit on the host with the engineer's suggested conventional message.
5. Handle the engineer's result:
   - `DONE`: run `python -m omi run omi-agent-reviewer <ID>` (fresh instance in a read-only container; it first runs tests, scope and skills checks and, if one fails, reports it instead of starting: treat that as a fix round; skip it for docs-only or `.omi/`-only changes).
   - Review `FAIL`: write the findings under `## Checkpoint` in `<wt>`'s task file, commit, and run step 3 again. After 2 failed fix rounds, ask the PO.
   - `NEEDS SCOPE`: if it fits the task goal, widen `scope` in the task file, commit it on `development` too (the scope is read from there), and rerun. Otherwise ask the PO.
6. On PASS, set `status: done` in `<wt>`'s task file and commit. Then:
   - With a GitHub remote: `git -C <wt> push -u origin task/<ID>`, `gh pr create --base development --head task/<ID> --fill`, then `gh pr checks --watch`. If CI fails, that counts as a fix round (step 5). When green, run `gh pr merge --squash --delete-branch`, then `git pull`.
   - Without a remote: `git merge --squash task/<ID>`, then commit `<type>: <title> (<ID>)`.
7. Post-merge check: run the project's test command on `development`. Then remove `<wt>` and `task/<ID>` if still present (`gh pr merge --delete-branch` already does both), and clean up: if `python -m omi status` shows no planned task left, run `python -m omi clean --all` (also removes the cached worker image); otherwise run `python -m omi clean` and keep the image as cache for the next task.
8. Report to the PO in at most 10 lines and stop. The PO picks the next task.
