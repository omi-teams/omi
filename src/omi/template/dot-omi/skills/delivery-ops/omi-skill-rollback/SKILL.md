---
id: omi-skill-rollback
group: delivery-ops
description: Use when a released candidate or main is bad and must be undone, by reverting the promotion merge or redeploying the previous rc tag.
tokens: 541
tools: Read, Bash
source_repo: https://github.com/omi-teams/omi-squad2
source_ref: a35ba0957a0a8e7e431fbbaba2b3df1f3588a79d
source_file: .claude/skills/omi-release/SKILL.md, .omi/tasks/TASK-010.md, .omi/tasks/TASK-018.md
source_license: internal (no LICENSE file yet)
source_use: rewrite
---
# Rollback

Based on the rollback line every `omi-release` PR carries: revert the promotion merge commit on staging (or main), or redeploy the previous `rc-*` tag.

## When to use
- The PO or UAT found a release candidate or `main` bad and wants it undone.

## When not to use
- A bug that a normal fix task can correct before promotion: use a task.
- No release was merged yet: close the PR instead.

## Inputs
- The promotion PR, its merge commit SHA, and the previous `rc-*` tag (`git tag --list 'rc-*' --sort=-creatordate`).

## Steps
1. Find the merge commit: `git log --merges --oneline -5 origin/<branch>`. Promotion PRs are merge commits (squash would make this revert impossible; see `omi-skill-release-checklist`).
2. Choose with the PO: (a) revert, or (b) redeploy the previous `rc-*` tag (no git change, deploy is outside omi).
3. For (a): in a task worktree branch from the target, `git revert -m 1 <merge-sha>`, run the project tests, open a PR to the same base. Do not push to staging or main; the PO merges (ruleset `omi-po-only`).
4. Do not delete, move or retag existing `rc-*` or `v*` tags (tag ruleset, TASK-010). A rolled-back release keeps its tag; the next release gets a new one.
5. Record the incident and the revert commit in a task checkpoint; reverting a revert later re-applies the change, so note that in the PR.

## Outputs and evidence
- Revert PR URL, the reverted merge SHA, test output of the reverted tree.

## Stop and escalate
- The merge was squashed or rebased, or the revert conflicts: stop and report to the PO; do not force-push.
- Data or deploy state is involved: stop, that is not a git matter.

## Tools needed
- Read, Bash (`git`, `gh`).
