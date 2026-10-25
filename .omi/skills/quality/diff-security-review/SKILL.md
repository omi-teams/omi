---
id: diff-security-review
group: quality
description: Use when reviewing a code change for security regressions, especially auth, input handling, secrets, crypto or dependency changes.
tokens: 638
tools: Read, Grep, Bash
source_repo: https://github.com/trailofbits/skills
source_ref: 196a9073ab10d35bacf111f945e02c00b2c6883a
source_file: plugins/differential-review/skills/differential-review/SKILL.md
source_license: CC-BY-SA-4.0
source_use: rewrite
---
<!-- Own wording, ideas only from Trail of Bits "differential-review" (https://github.com/trailofbits/skills, CC-BY-SA-4.0, commit 196a9073ab10d35bacf111f945e02c00b2c6883a). No text copied. -->
# Diff security review

Source: ideas only (Trail of Bits differential-review).

## When to use
- A change touches authentication, authorization, parsing of external input, secrets, crypto, file or process access, or dependencies.

## When not to use
- Documentation-only or test-only changes; a full audit of an untouched codebase.

## Inputs
- The diff, the task file, and read access to the callers of every changed function.

## Steps
1. Size the change. Small: read every changed line. Large: start with the high-risk files from step 2 and say what you skipped.
2. Rank risk: removed checks or validation, new external input, changed permission logic, new dependency or version bump, secrets or config, shell/SQL/path construction.
3. Use history: look at why a removed or changed guard was added (`git log -S`, `git blame`). Treat an unexplained removal as suspect.
4. For each risky hunk, find the callers and the data path from untrusted source to sink. Check what the change does to that path.
5. Look for what the diff does not show: callers that relied on old behaviour, error paths that now skip a check.
6. Write findings as `file:line | severity | reason | how verified` (code read, caller grep, test or reproduction). Do not report guesses as findings; list them as questions.
7. Do not accept "internal only", "tests pass" or "the framework handles it" without reading the code that proves it.

## Outputs and evidence
- Findings with location, reason, severity and how each was verified; a list of unreviewed files; a verdict.

## Stop and escalate
- A confirmed exploitable flaw, a leaked secret, or a removed access check you cannot explain: stop and report immediately; do not publish details beyond the task report.
- Evidence needs running untrusted code or network access not granted: report NEEDS SCOPE.

## Tools needed
- Read, Grep, Bash (read-only git and test commands).
