---
id: TASK-076
title: Worker runtime for compiled languages - exec cache tmpfs, sizes in config, PATH for login shells
status: planned
depends:
scope: src/omi/__init__.py, tests/**, src/omi/template/**, docker/**
role: omi-agent-engineer
skills: [omi-skill-docker-worker-pitfalls, omi-skill-windows-powershell]
refs:
plan: PLAN-001
tool:
model: sonnet
effort: medium
workflow: omi-flow-feature-sensitive
step:
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
Done:
Not done:
Tests:
Next:
