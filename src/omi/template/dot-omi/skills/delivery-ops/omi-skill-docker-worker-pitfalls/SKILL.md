---
id: omi-skill-docker-worker-pitfalls
group: delivery-ops
description: Use when an omi worker or run container fails, cannot write, cannot run git or the CLI, leaves containers or images behind, or when changing the worker Dockerfile.
tokens: 706
tools: Read, Bash
source_repo: https://github.com/omi-teams/omi
source_ref: a35ba0957a0a8e7e431fbbaba2b3df1f3588a79d
source_file: docs/spikes/docker.md, .omi/tasks/TASK-006.md, .omi/tasks/TASK-015.md, .omi/tasks/TASK-018.md, src/omi/template/docker/Dockerfile, src/omi/template/docker/prove.sh
source_license: internal (no LICENSE file yet)
source_use: rewrite
---
# Docker worker pitfalls

All points below are recorded in `docs/spikes/docker.md` (TASK-006) or the task files named.

## When to use
- `omi worker` or `omi run` fails, a write is denied, a CLI exits 126, or containers/images pile up.
- Editing `docker/Dockerfile` or the run flags.

## When not to use
- General Docker questions not about this worker: only the repo facts are covered.

## Inputs
- The failing command and output; `python -m omi worker <wt> --prove` result.

## Steps
1. Exit 126 on a CLI: it sits on a `noexec` tmpfs. CLIs must be baked into the image rootfs (the Dockerfile installs `@anthropic-ai/claude-code` at a pinned version).
2. Writes fail except in `/work`: expected. Rootfs is read-only; `/tmp` and `/home/node` are noexec tmpfs; flags `--read-only --cap-drop ALL --no-new-privileges`, user `node`. Do not loosen them to make a task pass; report NEEDS SCOPE.
3. `git` fails inside the container: expected. The worktree `.git` file points to a host path that is not mounted and is mounted read-only. The container edits files; the Coordinator runs git on the host after the run (TASK-015).
4. Token: only through the `CLAUDE_CODE_OAUTH_TOKEN` env var (name only in argv); never in the image, logs or git. `omi token set` stores it in Windows Credential Manager. Docker down or no token: stop, no host fallback.
5. `claude -p` waits for stdin: the runner redirects it from `/dev/null`. It needs `--permission-mode bypassPermissions` because the container is the boundary.
6. Boundary check: `--prove` must show all PASS; "write to main checkout" passes by absence, not denial.
7. Leftovers: containers use `--rm`; images are `omi-worker-<repo>:<dockerfile hash>`; `python -m omi clean` removes this repo's containers and stale images by label `omi-repo` (exact match, TASK-018: name prefix once matched another repo).
8. Changing the Dockerfile changes the hash and triggers a rebuild.

## Outputs and evidence
- `--prove` output, `docker ps -a --filter label=omi-worker=1` after the run (empty).

## Stop and escalate
- Docker is not running, no token, or the fix needs weaker flags or a host mount: stop and tell the PO.

## Tools needed
- Read, Bash (`docker`, `python -m omi`).
