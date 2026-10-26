---
id: omi-flow-promote
summary: Promote an accepted staging candidate - staging -> main PR, then the v<YYYY.MM.DD> tag after the PO merges. Use after the PO merged the release PR into staging and accepted it.
steps:
- id: promote | role: coordinator | skills: omi-skill-release-checklist, omi-skill-rollback | input: merged staging PR with rc, origin/main, origin/staging | output: PR staging -> main reusing release notes and rollback plan, URL reported | gate: none | stop: staging PR not MERGED, nothing to promote, or a main PR is open (report why and stop); else PR URL reported in at most 3 lines
- id: merge-main | role: coordinator | skills: | input: PR URL, rc | output: PO approval line in ## Steps; PO merges main with "Create a merge commit" | gate: po | stop: PO merged the PR (nothing merges into main except the PO)
- id: tag | role: coordinator | skills: omi-skill-release-checklist | input: merged main, origin/staging | output: pushed tag `<v>` | gate: none | stop: tree mismatch reported and stopped, or `<v>` reported in one line
---
# Promote and tag

**When to use:** the PO accepted the candidate on staging. Old `omi-release` phases 2 (promote) and 3 (tag).
**Use instead:** `omi-flow-release` to prepare a new candidate.

Never merge into staging or main (ruleset `omi-po-only`: only admin merges). Open the PR and stop. The PO must merge promotion PRs with "Create a merge commit", never squash or rebase, or staging/main diverge from development and the next release range and the revert-merge rollback break. Deploy is out of scope (stack-specific).

## promote (old 2.1-2.4)
1. `git fetch origin --tags`. Run `gh pr list --base staging --state all --limit 1 --json state,body`. Require `state == "MERGED"`; read `<rc>` from the body. Also require `git log origin/main..origin/staging` to be non-empty. Otherwise report why and stop.
2. Run `gh pr list --base main --state open`. If any is open, report it and stop.
3. `gh pr create --base main --head staging --title "release: <rc>" --body-file <file>`. The body points to the same `<rc>`, reuses the release notes and rollback plan, tells the PO (Vietnamese) to choose "Create a merge commit", and states that staging was accepted by the PO.
4. Report the PR URL in at most 3 lines and stop. The PO merges it, then tells you to run the `tag` step (`/omi-release tag`).

## tag (old 3.1-3.4, after the PO merges staging -> main)
1. `git fetch origin --tags`. Require `git diff --quiet origin/main origin/staging` (origin/main's tree equals the candidate's, ignoring merge commits). Otherwise report the mismatch and stop.
2. Set `<v>` = `v<YYYY.MM.DD>` (today). If `git ls-remote --tags origin <v>` shows it, use `<v>.2`, `<v>.3`, ... the first one that does not exist.
3. `git tag <v> origin/main` then `git push origin <v>`. Never move, force-push or delete an existing tag.
4. Report `<v>` in one line and stop.

## Models
- promote, tag: Coordinator, sonnet/low (needs `gh` and `git push` on the host).

## PO gates
`merge-main` needs `PO approval merge-main: <PO's words>` under `## Steps`; `omi step` refuses otherwise. The merge itself is the PO's.
