---
id: TASK-001
title: Add CI workflow running the self-check test
status: done
depends:
scope: .github/workflows/**
---
## Goal
Every PR into `development`, `staging` or `main` runs the test suite on GitHub Actions.

## Acceptance criteria
- [x] Workflow `.github/workflows/ci.yml` triggers on `pull_request` to development/staging/main and on push to development.
- [x] Runs on `ubuntu-latest` only, Python 3.13 (minimum supported; keeps Actions minutes low).
- [x] Installs the package (`pip install .`) and runs `python tests/test_omi.py`.
- [x] Job is named `test` (stable name for a required status check).

## Checkpoint
Done: ci.yml committed (0421615)
Not done: -
Tests: test_omi.py exit 0 locally; YAML parsed; not yet run on Actions
Next: review, PR, CI
