---
id: TASK-018
title: Make omi github require the repo's real CI check names
status: planned
depends: TASK-017
scope: src/omi/__init__.py, tests/**, docs/pilot.md
---
## Goal
In the pilot, staging/main required a check named `test`, but the matrix CI reports `test (ubuntu-latest)` and the other OS variants, so the gate could never pass and the PO had to bypass it.

## Acceptance criteria
- [ ] `omi github` takes the required check names from the latest CI run on `development` (check-run names), not a hard-coded `test`. If none exist yet, it says so and keeps the rule without required checks rather than requiring a name that never appears.
- [ ] Re-running after CI changes updates the required checks (and prints `unchanged` when they match).
- [ ] docs/pilot.md records: the check-name mismatch; UAT done by the Coordinator and accepted by the PO via bypass merge; and CI running twice per PR (push + pull_request on task branches).
- [ ] Tests cover the name discovery with `gh` stubbed.

## Checkpoint
Done:
Not done:
Tests:
Next:
