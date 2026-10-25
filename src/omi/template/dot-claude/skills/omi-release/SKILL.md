---
name: omi-release
description: Prepare a UAT release - rc tag, development -> staging PR, then staging -> main PR. The PO only tests and merges.
argument-hint: "[promote]"
disable-model-invocation: true
---
Phase: $ARGUMENTS. Empty = phase 1 (candidate). `promote` = phase 2 (staging -> main).

`staging` and `main` have ruleset `omi-po-only` (PR + check `test`; only admin merges). Never merge, push or force-push to them. Open the PR and stop. Deploy is out of scope (stack-specific).

Phase 1 - candidate:
1. `git fetch origin --tags`. Run `gh pr list --base staging --state open`. If any PR is open, report it to the PO and stop (one candidate at a time).
2. Run `git log --oneline origin/staging..origin/development`. If empty, report "nothing to release" and stop.
3. Check `origin/development` is green (`gh run list --branch development --limit 1`, status success). If not, report and stop.
4. Tag `rc-<YYYYMMDD>-<sha7>` on `origin/development` (sha7 = `git rev-parse --short=7 origin/development`): `git tag <rc> origin/development`, `git push origin <rc>`.
5. Collect task IDs with `status: done` changed in that range (`git diff --name-only origin/staging origin/development -- .omi/tasks`, then read each file).
6. Write the PR body in Vietnamese for the PO:
   - Release notes: the commit list from step 2 plus the task IDs and titles.
   - Test guide: per task, its acceptance criteria as a "what to try / expected result" checklist.
   - Rollback: revert the promotion merge commit on staging (or main), or redeploy the previous `rc-*` tag.
   - The rc tag name.
7. `gh pr create --base staging --head development --title "release: <rc>" --body-file <file>`.
8. Report to the PO in at most 5 lines: PR URL, rc tag, "test, then merge the PR yourself". Stop.

Phase 2 - promote (only after the PO merged the staging PR):
1. Run `gh pr list --base staging --state merged --limit 1 --json body,mergedAt` and read the rc tag from its body. If the latest staging PR is not merged, tell the PO and stop.
2. Run `gh pr list --base main --state open`. If any is open, report it and stop.
3. `gh pr create --base main --head staging --title "release: <same rc>" --body-file <file>`. The body points to the same rc tag, reuses the release notes and rollback plan, and states that staging was accepted by the PO.
4. Report the PR URL in at most 3 lines and stop. The PO merges it.
