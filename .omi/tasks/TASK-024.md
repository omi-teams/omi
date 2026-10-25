---
id: TASK-024
title: Skill group - quality and security
status: in-progress
depends: TASK-022
scope: .omi/skills/quality/**, .omi/skills/CATALOG.md, docs/research/_src/**, tests/test_omi.py, src/omi/template/dot-omi/skills/quality/**, .omi/decisions.md
---
## Goal
Skills for reviewer and engineer evidence: verification, debugging, diff security review, over-engineering review.

## Acceptance criteria
- [ ] Skills: `verify-evidence` (Superpowers verification idea), `debug-root-cause`, `diff-security-review` and `ci-workflow-audit` (ideas from Trail of Bits, CC-BY-SA: rewritten, source cited, no verbatim text), `simplify-review` (Ponytail ideas).
- [ ] Each findings-style skill requires location + reason + how it was verified, and says when to stop and escalate.
- [ ] Each passes `--check`, is at most 2000 tokens, and records source, commit, file, license and use.
- [ ] Catalog regenerated; the template copy is identical.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-025
