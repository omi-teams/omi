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
step: architect
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

## Steps
- plan started 2026-10-26 21:07
- plan done 2026-10-26 21:07
- architect started 2026-10-26 21:07

## Reports
2026-10-26 21:09 omi-agent-architect (claude):
> ```
> RECOMMEND: B - worker_argv takes explicit cache_mb/tmp_mb (default 2048/512), and one helper worker_sizes(main) reads .omi/config.json "worker" for all 3 callers (run_role, run_hook, worker --prove); the argv stays a pure function, so tests need no config fixture.
> OPTIONS: A (worker_argv reads config itself via main_checkout(wt)): fewer call-site edits / hidden file IO in a pure argv builder, existing argv tests start depending on disk; B (explicit params + helper): 3 one-line call-site edits / none; C (module constants overridden at config load): smallest diff / global state the python rule forbids, and run_hook/run_role read config separately anyway
> [... truncated ...]
> ```

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 14 | 4374 | 199813 | 70s | - | n/a |
