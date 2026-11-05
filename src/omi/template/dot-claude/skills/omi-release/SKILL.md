---
name: omi-release
description: Prepare a UAT release - rc tag, development -> staging PR, then staging -> main PR. The PO only tests and merges.
argument-hint: "[promote|tag]"
disable-model-invocation: true
---
Phase: $ARGUMENTS. Empty = run workflow `omi-flow-release` (candidate, verify, pr). `promote` = run `omi-flow-promote` from step `promote`. `tag` = run `omi-flow-promote` from step `tag` (after the PO merges staging -> main).

Read `.omi/workflows/<workflow>.md` and follow its steps exactly.

Never merge into staging or main (ruleset `omi-po-only`: only admin merges). Before the PR, run the `verify` step on the whole range `origin/staging..origin/development` (tests, CI, plan done criteria, open bugs and Known issues, structure check, real run of changed features); if anything fails or is unproven, stop and report unless the PO accepts the gaps. Then open the PR and stop. The PO must merge promotion PRs with "Create a merge commit", never squash or rebase.

Promotion PRs use `gh pr create --title ... --body-file ...` (never `--fill`). Title: `[RELEASE vX.Y.Z] development -> staging`, then `[RELEASE vX.Y.Z] staging -> main`. Body sections, in order: `## Summary`, `## Changes`, `## Not in this PR`, `## Verification`, `## Known issues` (or `none`), as in omi-task.
