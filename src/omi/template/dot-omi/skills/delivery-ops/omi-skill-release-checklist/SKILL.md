---
id: omi-skill-release-checklist
group: delivery-ops
description: Use when preparing, promoting or tagging a release (rc tag, development -> staging -> main PRs, v* tag) or checking a release PR before the PO tests it.
tokens: 653
tools: Read, Bash
source_repo: https://github.com/omi-teams/omi-squad2
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
3. Required checks: the ruleset must list the real check-run names of the latest CI run (pilot problem 6: a required `test` never matched `test (ubuntu-latest)` and the PO had to bypass). If `omi github` says no CI run exists yet, the rule has no required checks; say so in the PR.
4. The PR body (Vietnamese) holds: commit list, task IDs, per-task test checklist from acceptance criteria, rollback line, `<rc>`, and "Create a merge commit".
5. Never merge staging or main yourself and never squash or rebase promotion PRs: the PO merges, with a merge commit, or later ranges and the revert-merge rollback break.
6. Tag after the PO merge: `origin/main` tree equals `origin/staging` (`git diff --quiet`); `v<YYYY.MM.DD>`, then `.2`, `.3` if taken. Never move, force-push or delete a tag; the tag ruleset on `rc-*` and `v*` (TASK-010) allows only the admin.
7. CI runs twice per PR on task branches (push + pull_request, pilot problem 7): a double run is known, not a failure.

## Outputs and evidence
- PR URL, `<rc>`, and the command output of steps 1, 2 and 6 (`gh pr list`, `git log`, `git diff --quiet`).

## Stop and escalate
- An open PR, an empty range, or a tree mismatch on tagging: report and stop.
- Any merge, bypass or tag deletion would be needed: that is the PO's action; stop.

## Tools needed
- Read, Bash (`git`, `gh`).
