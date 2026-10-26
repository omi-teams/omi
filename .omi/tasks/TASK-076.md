---
id: TASK-076
title: Worker runtime for compiled languages - exec cache tmpfs, sizes in config, PATH for login shells
status: in-progress
depends:
scope: src/omi/__init__.py, tests/**, src/omi/template/**, docker/**, .claude/skills/omi-idea/SKILL.md
role: omi-agent-engineer
skills: [omi-skill-docker-worker-pitfalls, omi-skill-windows-powershell]
refs:
plan: PLAN-001
tool:
model: sonnet
effort: medium
workflow: omi-flow-feature-sensitive
step: build
---
## Goal
Gaps #3 #5 #15 #17 #18 #22 (omi-board session 97bfceb1): Go tests and builds fail in worker, reviewer and hook containers (noexec tmpfs, 256 MB, PATH lost in `bash -lc`, no dependency cache). Give every omi container a sized, exec-allowed cache and keep the toolchain on PATH.

## Acceptance criteria
- [ ] Every omi container (engineer, read roles, hooks) gets a tmpfs `/cache` mounted `rw,exec,nosuid,uid=1000,gid=1000` with size `worker.cache_mb` from `.omi/config.json` (default 2048), and env `XDG_CACHE_HOME=/cache`, `GOCACHE=/cache/go-build`, `GOMODCACHE=/cache/go-mod`, `npm_config_cache=/cache/npm`, `PIP_CACHE_DIR=/cache/pip`. `/tmp` and `/home/node` stay noexec; their size is `worker.tmp_mb` (default 512). Tested on the docker argv.
- [ ] A compiled test binary can run from `/cache` (Coordinator real check in a Go sandbox on the Windows host; unit test asserts the mount flags).
- [ ] Template `docker/Dockerfile` writes `/etc/profile.d/omi-path.sh` that keeps the image PATH, so `bash -lc 'command -v node'` and any toolchain added via `ENV PATH` still resolve. This repo's `docker/Dockerfile` gets the same change.
- [ ] Template Dockerfile has a commented example block for adding a toolchain (Go: download, `ENV PATH`), and `.claude/skills/omi-idea/SKILL.md` (root and template) says TASK-001 adds the chosen stack's toolchain and its `network_allow` registries to the worker.
- [ ] `omi status` prints one line per running omi container whose `/cache` or `/home/node` is over 90% full (best effort via `docker exec df`; silent without docker). Tested with a fake subprocess.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done: all criteria implemented (worker_argv cache tmpfs/env, worker_sizes, Dockerfile profile.d + Go example, omi-idea skill, status full_volumes) with tests.
Not done: Windows host run and real Go check (Coordinator).
Tests: python3 tests/test_omi.py ok on Linux.
Next: Coordinator review and commit.

## Steps
- plan started 2026-10-26 21:07
- plan done 2026-10-26 21:07
- architect started 2026-10-26 21:07
- architect done 2026-10-26 21:09
- build started 2026-10-26 21:09

## Reports
2026-10-26 21:09 omi-agent-architect (claude):
> ```
> RECOMMEND: B - worker_argv takes explicit cache_mb/tmp_mb (default 2048/512), and one helper worker_sizes(main) reads .omi/config.json "worker" for all 3 callers (run_role, run_hook, worker --prove); the argv stays a pure function, so tests need no config fixture.
> OPTIONS: A (worker_argv reads config itself via main_checkout(wt)): fewer call-site edits / hidden file IO in a pure argv builder, existing argv tests start depending on disk; B (explicit params + helper): 3 one-line call-site edits / none; C (module constants overridden at config load): smallest diff / global state the python rule forbids, and run_hook/run_role read config separately anyway
> [... truncated ...]
> ```
2026-10-26 21:11 omi-agent-engineer (claude):
> DONE
> - Files: `src/omi/__init__.py`, `tests/test_omi.py`, `docker/Dockerfile`, `src/omi/template/docker/Dockerfile`, `.claude/skills/omi-idea/SKILL.md`, `src/omi/template/dot-claude/skills/omi-idea/SKILL.md`, `.omi/tasks/TASK-076.md`
> - Worker argv: `worker_argv` mounts `/cache` with `rw,exec,nosuid,uid=1000,gid=1000` and the five cache env vars. `/tmp` and `/home/node` stay noexec. Sizes come from `worker.cache_mb` and `worker.tmp_mb` in `.omi/config.json` (defaults 2048 and 512) through the new `worker_sizes(main)`. The three callers pass them.
> - Dockerfile: the repo and template Dockerfiles are identical, so `omi status` doesn't flag drift. Both write `/etc/profile.d/omi-path.sh` and carry a commented Go toolchain example. Any `ENV PATH` line must sit above the profile line, and a comment says so.
> - `omi-idea` skill: root and template now say TASK-001 adds the stack's toolchain to `docker/Dockerfile` and its registries to `network_allow`.
> - Status: `omi status` prints a line for each running container whose `/cache` or `/home/node` is over 90% full. It uses `docker exec df`.
> - Tests: `python3 tests/test_omi.py` passes on Linux. I added `test_worker_cache_tmpfs_and_full_volumes` and updated `test_hooks`, whose env-list assertion now includes the cache vars. The Windows run and the real Go test from `/cache` are not done; they are the Coordinator's checks.
> - Suggested commit: `feat(worker): exec-allowed sized /cache tmpfs, PATH for login shells, full-volume warning in status`
> - Open issue: I haven't built the image, so the `profile.d` change is untested in a real container.
2026-10-26 21:11 hook post-run passed:
> Conflict. The container name "/tmp000yj30n-TASK-001-engineer-codex-gpt-x-medium-141109" is already in useBind for 0.0.0.0:8080 failed: port is already in usewrote /tmp/tmp7btl5e4y/.omi/skills/CATALOG.md (2 skills)
> create AGENTS.md
> create docker/Dockerfile
> create docker/prove.sh
> create docker/proxy.py
> create .claude/settings.json
> create .claude/skills/omi-idea/SKILL.md
> create .claude/skills/omi-release/SKILL.md
> create .claude/skills/omi-status/SKILL.md
> create .claude/skills/omi-task/SKILL.md
> create .omi/agents/CATALOG.md
> create .omi/agents/omi-agent-architect.md
> create .omi/agents/omi-agent-designer-ui.md
> create .omi/agents/omi-agent-devops.md
> create .omi/agents/omi-agent-docs-writer.md
> create .omi/agents/omi-agent-engineer.md
> create .omi/agents/omi-agent-qa-tester.md
> create .omi/agents/omi-agent-researcher.md
> create .omi/agents/omi-agent-reviewer.md
> create .omi/agents/omi-agent-security-reviewer.md
> create .omi/config.json
> create .omi/decisions.md
> create .omi/hooks/post-run.sh
> create .omi/plans/CATALOG.md
> create .omi/plans/PLAN-000.md
> create .omi/references/CATALOG.md
> create .omi/references/nextjs-app-router.md
> create .omi/references/postgres-conventions.md
> create .omi/rules/CATALOG.md
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
> [... truncated ...]
> ok

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 14 | 4374 | 199813 | 70s | - | n/a |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 24 | 7218 | 357509 | 105s | 2/3 omi-skill-docker-worker-pitfalls omi-skill-lean-implementation | - |
