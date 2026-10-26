---
id: omi-flow-release
summary: Prepare a UAT release candidate - rc tag and the development -> staging PR with Vietnamese notes, test guide and rollback. Use when development has unreleased work; the PO tests and merges, then run omi-flow-promote.
steps:
- id: candidate | role: coordinator | skills: omi-skill-release-checklist | input: origin/development, origin/staging, open PRs | output: `<rc>` name and the list of done task IDs in the range | gate: none | stop: PR open on staging (report it and stop), or empty range (report "nothing to release" and stop), else rc and task list ready
- id: pr | role: coordinator | skills: omi-skill-release-checklist, omi-skill-rollback | input: rc, commit list, done tasks | output: PR body file (Vietnamese), PR development -> staging, rc tag pushed, report of PR URL and rc | gate: none | stop: PR URL and rc reported in at most 3 lines
- id: merge-staging | role: coordinator | skills: | input: PR URL, rc | output: PO approval line in ## Steps; PO tests and merges staging with "Create a merge commit" | gate: po | stop: PO merged the PR (nothing merges into staging except the PO)
---
# Release candidate

**When to use:** development has unreleased work and the PO wants a UAT candidate. Old `omi-release` phase 1.
**Use instead:** `omi-flow-promote` once the PO accepted staging.

Never merge into staging or main (ruleset `omi-po-only`: only admin merges). Open the PR and stop. The PO must merge promotion PRs with "Create a merge commit", never squash or rebase, or staging/main diverge from development and the next release range and the revert-merge rollback break. Deploy is out of scope (stack-specific).

## candidate (old 1.1-1.4)
1. `git fetch origin --tags`. Run `gh pr list --base staging --state open`. If any PR is open, report it to the PO and stop (one candidate at a time).
2. Run `git log --oneline origin/staging..origin/development`. If empty, report "nothing to release" and stop.
3. Set `<rc>` = `rc-<YYYYMMDD>-<sha7>` (sha7 = `git rev-parse --short=7 origin/development`).
4. Collect task IDs with `status: done` changed in that range (`git diff --name-only origin/staging origin/development -- .omi/tasks`, then read each file).

## pr (old 1.5-1.8)
5. Write the PR body in Vietnamese for the PO:
   - Release notes: the commit list from step 2 plus the task IDs and titles.
   - Test guide: per task, its acceptance criteria as a "what to try / expected result" checklist.
   - Rollback: revert the promotion merge commit on staging (or main), or redeploy the previous `rc-*` tag.
   - The tag name `<rc>`.
   - Merge instruction: choose "Create a merge commit" (not squash/rebase).
6. `gh pr create --base staging --head development --title "release: <rc>" --body-file <file>`.
7. Tag after the PR exists: if `git ls-remote --tags origin <rc>` shows it, skip. Otherwise create it if missing locally (`git rev-parse -q --verify refs/tags/<rc>` || `git tag <rc> origin/development`), then `git push origin <rc>`.
8. Report the PR URL and `<rc>` in at most 3 lines and stop. The PO tests and merges.

## Models
- candidate, pr: Coordinator, sonnet/low (needs `gh` and `git push` on the host).

## PO gates
`merge-staging` needs `PO approval merge-staging: <PO's words>` under `## Steps`; `omi step` refuses otherwise. The merge itself is the PO's.
