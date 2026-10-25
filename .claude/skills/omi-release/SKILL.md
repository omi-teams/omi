---
name: omi-release
description: Prepare a UAT release - rc tag, development -> staging PR, then staging -> main PR. The PO only tests and merges.
argument-hint: "[promote]"
disable-model-invocation: true
---
Phase: $ARGUMENTS. Empty = phase 1 (candidate). `promote` = phase 2 (staging -> main).

Never merge into staging or main (ruleset `omi-po-only`: only admin merges). Open the PR and stop. The PO must merge promotion PRs with "Create a merge commit", never squash or rebase, or staging/main diverge from development and the next release range and the revert-merge rollback break. Deploy is out of scope (stack-specific).

Phase 1 - candidate:
1. `git fetch origin --tags`. Run `gh pr list --base staging --state open`. If any PR is open, report it to the PO and stop (one candidate at a time).
2. Run `git log --oneline origin/staging..origin/development`. If empty, report "nothing to release" and stop.
3. Set `<rc>` = `rc-<YYYYMMDD>-<sha7>` (sha7 = `git rev-parse --short=7 origin/development`).
4. Collect task IDs with `status: done` changed in that range (`git diff --name-only origin/staging origin/development -- .omi/tasks`, then read each file).
5. Write the PR body in Vietnamese for the PO:
   - Release notes: the commit list from step 2 plus the task IDs and titles.
   - Test guide: per task, its acceptance criteria as a "what to try / expected result" checklist.
   - Rollback: revert the promotion merge commit on staging (or main), or redeploy the previous `rc-*` tag.
   - The tag name `<rc>`.
   - Merge instruction: choose "Create a merge commit" (not squash/rebase).
6. `gh pr create --base staging --head development --title "release: <rc>" --body-file <file>`.
7. Tag after the PR exists: if `git ls-remote --tags origin <rc>` shows it, skip. Otherwise create it if missing locally (`git rev-parse -q --verify refs/tags/<rc>` || `git tag <rc> origin/development`), then `git push origin <rc>`.
8. Report the PR URL and `<rc>` in at most 3 lines and stop. The PO tests and merges.

Phase 2 - promote:
1. `git fetch origin --tags`. Run `gh pr list --base staging --state all --limit 1 --json state,body`. Require `state == "MERGED"`; read `<rc>` from the body. Also require `git log origin/main..origin/staging` to be non-empty. Otherwise report why and stop.
2. Run `gh pr list --base main --state open`. If any is open, report it and stop.
3. `gh pr create --base main --head staging --title "release: <rc>" --body-file <file>`. The body points to the same `<rc>`, reuses the release notes and rollback plan, tells the PO (Vietnamese) to choose "Create a merge commit", and states that staging was accepted by the PO.
4. Report the PR URL in at most 3 lines and stop. The PO merges it.
