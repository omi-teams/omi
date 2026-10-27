---
id: TASK-086
title: Download caches live in the worktree so hooks and reviewers see the engineer's dependencies
status: in-progress
depends:
plan: PLAN-001
scope: src/omi/__init__.py, tests/test_omi.py, .gitignore, README.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: sonnet
effort: medium
workflow: omi-flow-feature
step: build
---
## Goal
Gap #17 (omi-board session 97bfceb1): the post-run hook and read roles cannot use the dependencies the engineer downloaded (Go modules, npm, pip), because each container has its own `/cache` tmpfs (TASK-076) that disappears when the container stops. PO decision 2026-10-27: put the download caches inside the worktree at `/work/.omi-cache/` (gitignored); the engineer writes them, the hook and read roles read them through the existing read-only worktree mount. No new mounts or Docker volumes; the cache goes away with the worktree. Build caches (GOCACHE, XDG_CACHE_HOME) stay in the `/cache` tmpfs.

## Acceptance criteria
- [x] Every omi container (write role, read roles, hooks) gets `GOMODCACHE=/work/.omi-cache/go-mod`, `npm_config_cache=/work/.omi-cache/npm`, `PIP_CACHE_DIR=/work/.omi-cache/pip` and `GOFLAGS=-modcacherw` (so Windows can delete the worktree); `GOCACHE` and `XDG_CACHE_HOME` stay under `/cache`. Tested on the docker argv for a write role, a read role and a hook.
- [x] `.omi-cache/` is gitignored: `omi init` and `omi upgrade --apply` add it to `.gitignore` when missing (same helper style as `__pycache__/`); this repo's `.gitignore` has it. Files under `.omi-cache/` never count as out-of-scope changes. Tested.
- [ ] `git worktree remove` of a worktree holding a Go module cache works on the Windows host (Coordinator real check in a sandbox: write a read-only file tree under `.omi-cache/go-mod` as Go would without -modcacherw, and confirm -modcacherw files remove cleanly; or run `go mod download` in a worker if Go is in the image).
- [x] README: one Vietnamese line on where download caches live and why.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done: Shared worker cache environment updated for write/read roles and hooks; GOFLAGS=-modcacherw; init/upgrade gitignore helper; cache scope exemption (existing symlink protection retained); Vietnamese README line; regression tests added.
Not done: -
Coordinator: Windows host suite passed (ok); sandbox check on Windows host: read-only tree under .omi-cache/go-mod blocks `git worktree remove` (Permission denied), writable tree (-modcacherw) removes cleanly.
Tests: python3 tests/test_omi.py PASSED on Linux (exit 0, ok), including write/read/hook argv, init/upgrade ignore idempotency and actual Git ignore matching, cache scope filtering and README checks; Windows validation pending.
Next: Coordinator reviews diff and runs Windows host suite plus real Go cache worktree-removal sandbox check; no worker commit made. After merge: omi-release 0.3.0, then real /omi-upgrade check on omi-board (PLAN-001 done criteria).

## Steps
- plan started 2026-10-27 21:36
- plan done 2026-10-27 21:36
- build started 2026-10-27 21:36

## Reports
2026-10-27 21:41 omi-agent-engineer (codex):
> DONE — implementation complete; checkpoint updated.
> Files: `src/omi/__init__.py`, `tests/test_omi.py`, `.gitignore`, `README.md`, `.omi/tasks/TASK-086.md`.
> Suggested commit: `fix(worker): share download caches through the worktree`
> Tests: `python3 tests/test_omi.py` passed on Linux (exit 0).
> Open issues: Coordinator must run Windows tests and real Go cache worktree-removal check.
> No commit made.
2026-10-27 21:43 hook post-run passed:
> create AGENTS.md
> create docker/Dockerfile
> create docker/prove.sh
> create docker/proxy.py
> create .claude/settings.json
> create .claude/skills/omi-idea/SKILL.md
> create .claude/skills/omi-release/SKILL.md
> create .claude/skills/omi-status/SKILL.md
> create .claude/skills/omi-task/SKILL.md
> create .claude/skills/omi-upgrade/SKILL.md
> create .omi/agents/omi-agent-architect.md
> create .omi/agents/omi-agent-designer-ui.md
> create .omi/agents/omi-agent-devops.md
> create .omi/agents/omi-agent-docs-writer.md
> create .omi/agents/omi-agent-engineer.md
> create .omi/agents/omi-agent-qa-tester.md
> create .omi/agents/omi-agent-researcher.md
> create .omi/agents/omi-agent-reviewer.md
> create .omi/agents/omi-agent-security-reviewer.md
> create .omi/hooks/post-run.sh
> create .omi/plans/PLAN-000.md
> create .omi/references/nextjs-app-router.md
> create .omi/references/postgres-conventions.md
> create .omi/rules/docker.md
> create .omi/rules/go.md
> create .omi/rules/nextjs.md
> create .omi/rules/postgres.md
> create .omi/rules/python.md
> create .omi/skills/.gitkeep
> create .omi/skills/data/omi-skill-data-review/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-docker-worker-pitfalls/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-incident/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-release-checklist/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-rollback/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-windows-powershell/SKILL.md
> create .omi/skills/qa-web/omi-skill-web-qa/SKILL.md
> create .omi/skills/quality/omi-skill-ci-workflow-audit/SKILL.md
> create .omi/skills/quality/omi-skill-debug-root-cause/SKILL.md
> create .omi/skills/quality/omi-skill-diff-security-review/SKILL.md
> create .omi/skills/quality/omi-skill-simplify-review/SKILL.md
> create .omi/skills/quality/omi-skill-verify-evidence/SKILL.md
> create .omi/skills/ui/omi-skill-ui-a11y-review/SKILL.md
> create .omi/skills/ui/omi-skill-ui-direction/SKILL.md
> create .omi/skills/ui/omi-skill-ui-direction/references/style-presets.md
> [... truncated ...]
> ok

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 1263284 | 5995 | 1199360 | 261s | 1/1 omi-skill-lean-implementation | - |
