---
id: omi-flow-promote
summary: Promote an accepted staging candidate - staging -> main PR, then the v<YYYY.MM.DD> and v<pyproject version> tags after the PO merges. Use after the PO merged the release PR into staging and accepted it.
steps:
- id: promote | role: coordinator | skills: omi-skill-release-checklist, omi-skill-rollback | input: merged staging PR with rc, origin/main, origin/staging | output: PR staging -> main reusing release notes and rollback plan, URL reported | gate: none | stop: staging PR not MERGED, nothing to promote, or a main PR is open (report why and stop); else PR URL reported in at most 3 lines
- id: merge-main | role: coordinator | skills: | input: PR URL, rc | output: PO approval line in ## Steps; PO merges main with "Create a merge commit" | gate: po | stop: PO merged the PR (nothing merges into main except the PO)
- id: tag | role: coordinator | skills: omi-skill-release-checklist | input: merged main, origin/staging | output: pushed date and version tags | gate: none | stop: tree mismatch reported and stopped, version tag conflict reported and stopped, or both tags reported in one line
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
2. Read `[project].version` from `origin/main:pyproject.toml`, never the working tree. Tag both `v<YYYY.MM.DD>` and `v<pyproject version>` on the main commit. Skip any tag already on the same commit (including annotated tags). For a date tag on another commit, try `.2`, `.3`, ...; for a version tag on another commit, stop before creating any tags and request a version bump. Never move, force-push or delete an existing tag.
3. After the fetch and tree check above, run this procedure with Python 3.13:

```python
from datetime import date
import subprocess
import tomllib


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True, encoding="utf-8").stdout.strip()


def target(tag):
    result = subprocess.run(["git", "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"],
                            capture_output=True, encoding="utf-8")
    return result.stdout.strip() if result.returncode == 0 else None


main = git("rev-parse", "origin/main")
version = "v" + tomllib.loads(git("show", "origin/main:pyproject.toml"))["project"]["version"]
if target(version) not in (None, main):
    raise SystemExit(f"{version} points to another commit; bump pyproject version before releasing")
base = "v" + date.today().strftime("%Y.%m.%d")
dated = base
suffix = 2
while target(dated) not in (None, main):
    dated = f"{base}.{suffix}"
    suffix += 1
for tag in dict.fromkeys((dated, version)):
    if target(tag) == main:
        continue
    git("tag", tag, main)
    git("push", "origin", f"refs/tags/{tag}")
print(f"{dated} {version}")
```

4. Report both tags in one line and stop; identify any tags skipped because they already point to main.

## Models
- promote, tag: Coordinator, sonnet/low (needs `gh` and `git push` on the host).

## PO gates
`merge-main` needs `PO approval merge-main: <PO's words>` under `## Steps`; `omi step` refuses otherwise. The merge itself is the PO's.
