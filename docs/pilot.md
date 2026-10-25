# Pilot (TASK-009): split-bill

2026-10-25. Claude Code 2.1.302, Windows 11. Product: `split-bill`, a stdlib Python CLI that splits a group bill.
Repo: [omi-teams/omi-pilot-splitbill](https://github.com/omi-teams/omi-pilot-splitbill), public, squad account has Write only.

## Result

| Step | Outcome |
|---|---|
| `omi init` in an empty folder | OK |
| `/omi-idea` | `docs/product.md` approved (`7157f3d`), 5 tasks planned |
| `omi github --po` | staging + 3 rulesets created; PO credential removed afterwards |
| `/omi-task TASK-001` (skeleton + CI) | PR #1 merged, CI green |
| `/omi-task TASK-002` (equal split) | PR #2 merged, CI green |
| `/omi-release` | PR #3 development → staging, tag `rc-20261025-4afcd6f`, test checklist in the PR |

## Tokens per role

From the pilot session transcripts. "Cache read" is context re-sent on each turn and dominates the volume.

| Role | Model | Turns | Cache write | Cache read | Output |
|---|---|---|---|---|---|
| Coordinator (idea, 2 tasks, release) | opus | 34 | 58,006 | 2,303,679 | 15,457 |
| Engineer TASK-001 | haiku | 9 | 50,704 | 366,896 | 5,117 |
| Engineer TASK-002 | sonnet | 5 | 46,269 | 169,754 | 2,792 |
| Reviewer TASK-001 | sonnet | 3 | 14,239 | 23,316 | 820 |
| Reviewer TASK-002 | sonnet | 3 | 14,932 | 23,109 | 1,129 |

The Coordinator accounts for 80% of cache reads and 61% of output, all on the session's default model (opus). OMI sets models for agents, not for the main session.

## PO interventions

8 PO messages in the pilot session, 7 of them scripted: `/omi-idea` with the idea, one answer pasting defaults for the Coordinator's questions, `ok` to approve the spec, 2× `/omi-task`, `/omi-release`. One extra: the first `/omi-idea` was sent with no idea text.
Outside the pilot session, the PO created the GitHub repo (the squad may not create public repos), switched it to public, and ran `omi github --po` once.

## Problems found

| # | Problem | Fix |
|---|---|---|
| 1 | `omi-idea` commits `main` and creates `development` but never pushes; the Coordinator of this repo pushed by hand. | TASK-014 |
| 2 | Order dependency: `omi github` must run after `main` is pushed, because the `main` ruleset blocks the direct push. Nothing tells the PO when to run it. | TASK-014 |
| 3 | The Coordinator runs on the session default model (opus here), the largest cost by far. | TASK-014 (PO decides the default) |
| 4 | `omi github --po` prints the switch-back line twice (`gh auth logout` already switches). Cosmetic. | TASK-014 |
| 5 | The PO created the repo as private; on the Free plan rulesets need a public repo, so the PO had to be told to switch. | TASK-014: `omi github` checks visibility first |
| 6 | The ruleset required a check named `test`, but the matrix CI reports `test (ubuntu-latest)` and the other OS variants, so the gate could never pass and the PO had to bypass it. | TASK-018: `omi github` takes the names from the latest check runs on `development`; with none yet it requires nothing |
| 7 | CI runs twice per PR (`push` and `pull_request` on task branches). | Noted; not changed |

## UAT and acceptance

The Coordinator did the UAT of the release candidate. The PO accepted it by merging the staging and main PRs with the admin bypass (because of problem 6).
