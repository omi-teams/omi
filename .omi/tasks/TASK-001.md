---
id: TASK-001
title: Add CI workflow running the self-check test
status: in-progress
depends:
scope: .github/workflows/**
---
## Goal
Every PR into `development`, `staging` or `main` runs the test suite on GitHub Actions.

## Acceptance criteria
- [ ] Workflow `.github/workflows/ci.yml` triggers on `pull_request` to development/staging/main and on push to development.
- [ ] Runs on `ubuntu-latest` only, Python 3.13 (minimum supported; keeps Actions minutes low).
- [ ] Installs the package (`pip install .`) and runs `python tests/test_omi.py`.
- [ ] Job is named `test` (stable name for a required status check).

## Checkpoint
Done: ci.yml committed (0421615)
Not done: -
Tests: test_omi.py exit 0 locally; YAML parsed; not yet run on Actions
Next: review, PR, CI
