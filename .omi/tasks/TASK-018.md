---
id: TASK-018
title: Real CI check names in omi github, and a v* tag after release
status: in-progress
depends: TASK-017
scope: src/omi/__init__.py, tests/**, docs/pilot.md, .claude/skills/omi-task/**, src/omi/template/dot-claude/skills/omi-task/**, .claude/skills/omi-release/**, src/omi/template/dot-claude/skills/omi-release/**
---
## Goal
In the pilot, staging/main required a check named `test`, but the matrix CI reports `test (ubuntu-latest)` and the other OS variants, so the gate could never pass and the PO had to bypass it.

## Acceptance criteria
- [ ] `omi github` takes the required check names from the latest CI run on `development` (check-run names), not a hard-coded `test`. If none exist yet, it says so and keeps the rule without required checks rather than requiring a name that never appears.
- [ ] Re-running after CI changes updates the required checks (and prints `unchanged` when they match).
- [ ] docs/pilot.md records: the check-name mismatch; UAT done by the Coordinator and accepted by the PO via bypass merge; and CI running twice per PR (push + pull_request on task branches).
- [ ] `omi-release` gets a phase `tag` (run after the PO merges staging -> main): it checks that `origin/main`'s tree equals the candidate's, then tags `origin/main` as `v<YYYY.MM.DD>` (append `.N` if that tag exists) and pushes it. It never moves or deletes an existing tag. Phase 2 tells the PO to run it after merging. The template and root skill copies are identical.
- [ ] (PO request) `omi worker` gives each container a readable name: `omi-<repo>-<task-id>-engineer-<HHMMSS>` (e.g. `omi-omi-squad2-TASK-018-engineer-143205`), `--prove` uses `...-prove-<HHMMSS>`; names are sanitized to Docker's `[a-zA-Z0-9_.-]`. The image keeps its label and is named `omi-worker-<repo>:<hash>`.
- [ ] (PO rule: no leftovers after a task) `omi clean` removes every container with label `omi-worker=1` for this repo and every `omi-worker-<repo>` image except the one matching the current Dockerfile hash; after a successful build `omi worker` removes older images of the same repo. The `omi-task` skill's final cleanup step runs `python -m omi clean` along with the worktree and branch removal (template and root copies identical).
- [ ] Tests cover the name discovery with `gh` stubbed.

## Checkpoint
Done: all criteria (ci_checks + rulesets(checks) in src/omi/__init__.py, omi-release phase 3 tag in both copies, docs/pilot.md, test_ci_checks_and_apply).
Not done: none.
Tests: python3 tests/test_omi.py passes.
Next: Coordinator review and commit.
Round 2 (Coordinator): the PO asked for readable container names (new criterion above). Everything else from round 1 is done and committed; only add the naming and its test.
Round 2 done: container_name() + --name in worker_argv, image omi-worker-<repo>:<hash>, test_container_names. python3 tests/test_omi.py passes.
Round 3 (review PASS, Coordinator asks for hardening): in `ci_checks()` (1) return [] only when development has no commits with check runs (404 or empty); any other gh error must abort `omi github` with a message, never drop required checks; (2) walk back from the latest development commit (up to 20) to the newest commit that has completed check runs, and use those names, so a fresh chore commit whose CI has not started does not remove the gate. Add tests for both.
Round 3 done: ci_checks walks back up to 20 commits, aborts on non-404 gh errors; tests added. python3 tests/test_omi.py passes.
Round 4 (Coordinator): PO rule, nothing left behind when a task is done. Add `omi clean` and the auto-removal of older images (criterion above), and update the omi-task skill cleanup step. Containers already use --rm.
