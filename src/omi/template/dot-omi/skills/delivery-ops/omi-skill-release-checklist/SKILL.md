---
id: omi-skill-release-checklist
group: delivery-ops
description: Use when preparing, promoting or tagging a release (rc tag, development -> staging -> main PRs, v* tag) or checking a release PR before the PO tests it.
tokens: 777
tools: Read, Bash
source_repo: https://github.com/omi-teams/omi
source_ref: a35ba0957a0a8e7e431fbbaba2b3df1f3588a79d
source_file: .claude/skills/omi-release/SKILL.md, .omi/tasks/TASK-018.md, docs/pilot.md
source_license: internal (no LICENSE file yet)
source_use: rewrite
---
# Release checklist

Companion to the `omi-release` skill (that skill is the procedure; this is the pre-flight and the traps). Origin: TASK-018 and the pilot in `docs/pilot.md`.

## When to use
- Before `/omi-release`, `/omi-release promote` or `/omi-release tag`, and when reviewing a release PR.

## When not to use
- Deploying: stack-specific, not covered by `omi-release`.
- Fixing a broken release: use `omi-skill-rollback` or `omi-skill-incident`.

## Inputs
- `git fetch origin --tags` done; the list of `status: done` tasks in `origin/staging..origin/development`.

## Steps
1. One candidate at a time: no open PR with base `staging` (phase 1) or base `main` (phase 2).
2. The range `origin/staging..origin/development` must be non-empty; otherwise report "nothing to release".
3. Verify the whole range before the PR (`verify` step, with `omi-skill-verify-evidence`): full tests on the host, CI green on development, each plan's done criteria really met (not just task status), open bugs/tasks and reviewer "Known issues", `omi structure check` when a map exists, a real run of the changed features, and a list of what is unproven. Any fail or unproven item: stop and report; the PR opens only when all pass or the PO accepts the gaps in words.
4. Required checks: the ruleset must list the real check-run names of the latest CI run (pilot problem 6: a required `test` never matched `test (ubuntu-latest)` and the PO had to bypass). If `omi github` says no CI run exists yet, the rule has no required checks; say so in the PR.
5. The PR body (Vietnamese) holds: commit list, task IDs, per-task test checklist from acceptance criteria, rollback line, `<rc>`, and "Create a merge commit".
6. Never merge staging or main yourself and never squash or rebase promotion PRs: the PO merges, with a merge commit, or later ranges and the revert-merge rollback break.
7. Tag after the PO merge: `origin/main` tree equals `origin/staging` (`git diff --quiet`); `v<YYYY.MM.DD>` and `v<pyproject version>` from `[project].version` in `origin/main:pyproject.toml`, both on origin/main. Skip tags already on the same commit (peel annotated tags); use `.2`, `.3` for date tags on other commits. If the version tag points elsewhere, stop before creating tags and request a version bump. Follow the runnable tag procedure in `omi-flow-promote`. Never move, force-push or delete a tag; the tag ruleset on `rc-*` and `v*` (TASK-010) allows only the admin.
8. CI runs twice per PR on task branches (push + pull_request, pilot problem 7): a double run is known, not a failure.

## Outputs and evidence
- PR URL, `<rc>`, and the command output of steps 1, 2, 3 and 7 (`gh pr list`, `git log`, `git diff --quiet`).

## Stop and escalate
- An open PR, an empty range, or a tree mismatch on tagging: report and stop.
- Any merge, bypass or tag deletion would be needed: that is the PO's action; stop.

## Tools needed
- Read, Bash (`git`, `gh`).
