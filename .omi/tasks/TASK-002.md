---
id: TASK-002
title: Ship prompt fixes found in the TASK-001 pilot
status: in-progress
depends: TASK-001
scope: src/omi/template/**, .claude/**, .gitattributes, AGENTS.md
---
## Goal
Land the fixes learned from running TASK-001, so the next task runs without the same friction.

## Acceptance criteria
- [ ] `engineer.md` (template + installed copy) says the agent's own task file is always writable.
- [ ] `omi-task` skill step 6 removes worktree/branch only if still present (`gh pr merge --delete-branch` already does it).
- [ ] `.gitattributes` with `* text=auto eol=lf` stops the LF/CRLF warnings.
- [ ] `engineer.md` and `reviewer.md` (template + installed copy) set `effort: medium` next to `model: sonnet` (alias, not pinned ID).
- [ ] AGENTS.md (template + installed copy) quota rules give the per-call choice in one line each: mechanical = `haiku` + effort `low`; default = `sonnet` + `medium`; architecture or failed review twice = `opus` + `high`. Also note that pinning a full model ID (e.g. `claude-opus-5-5`) is allowed when stable results matter, and give the Codex equivalent: `codex exec -m <model> -c model_reasoning_effort=<level>`.
- [ ] `python tests/test_omi.py` passes.

## Checkpoint
Done: the two prompt edits committed on `task/TASK-002` (engineer.md template + installed copy; omi-task step 6). `.gitattributes` with `* text=auto eol=lf` added.
Done: `effort: medium` added next to `model: sonnet` in engineer.md and reviewer.md (template + installed). AGENTS.md (root + template) quota rules give per-call model + effort lines, pinning note, and Codex equivalent.
Not done: nothing in scope.
Tests: `python tests/test_omi.py` exit 0.
Next: PO review and PR.
