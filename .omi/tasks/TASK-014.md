---
id: TASK-014
title: Fix pilot findings in omi-idea, omi github and the Coordinator model
status: done
depends: TASK-009
scope: src/omi/__init__.py, src/omi/template/**, .claude/skills/omi-idea/**, tests/**, README.md
---
## Goal
Remove the manual steps and the main cost found in the TASK-009 pilot (see docs/pilot.md).

## Acceptance criteria
- [x] `omi-idea` pushes `main` and `development` when a remote exists, then tells the PO to run `python -m omi github --po` once.
- [x] `omi github` stops with a clear message if the repo is private (rulesets need public on the Free plan).
- [x] `omi github --po` prints the switch-back line once.
- [x] The template sets the Coordinator session model to the value the PO chooses (decision in `.omi/decisions.md`), and README says how to override it.
- [x] Template and root copies of changed skills stay identical; tests pass.

## Checkpoint
Done: all 5 criteria (idea push step, private check, single switch, model sonnet + README, skills identical).
Not done: none.
Tests: python tests/test_omi.py ok.
Next: review.
