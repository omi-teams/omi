---
id: TASK-043
title: Worker containers show the exact model, version and effort
status: done
depends:
scope: src/omi/__init__.py, src/omi/template/**, .omi/config.json, tests/**, README.md
---
## Goal
A running worker container tells the PO which model (full ID), effort and role it uses, from its name and labels alone.

## Acceptance criteria
- [x] Container name: `omi-<repo>-<task>-<role>-<model-id>-<effort>-<HHMMSS>` with the full model ID (e.g. `claude-sonnet-5-5`), limited to Docker's `[a-zA-Z0-9_.-]`.
- [x] Aliases (`haiku`, `sonnet`, `opus`) are resolved to a full ID from a `models` map in `.omi/config.json` (template default: haiku=claude-haiku-5-5, sonnet=claude-sonnet-5-5, opus=claude-opus-5-5; PO can edit) and the full ID is the value passed to the harness, so the name is what actually runs. An unknown alias or a missing effort fails before the container starts, naming the value.
- [x] Labels on the container: `omi-role`, `omi-task`, `omi-model`, `omi-effort`, `omi-started`.
- [x] `python -m omi status` lists running worker containers with task, role, model, effort and age (nothing extra when none run).
- [x] The `prove` container is named the same way without a model (`-none-`); `omi clean` still finds all containers by `omi-worker` and `omi-repo` labels.
- [x] `python tests/test_omi.py` passes, covering name, alias resolution, unknown alias and the status listing (docker mocked).

## Checkpoint
Done: all criteria (name, aliases via .omi/config.json, labels, status listing, prove -none-, tests, README)
Not done: -
Tests: python3 tests/test_omi.py ok
Next: TASK-022
