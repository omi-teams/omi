---
id: TASK-015
title: Run the engineer inside the Docker worker in omi-task
status: in-progress
depends: TASK-006
scope: src/omi/__init__.py, src/omi/template/**, .claude/skills/omi-task/**, .claude/agents/engineer.md, docker/**, tests/**, README.md, AGENTS.md
---
## Goal
In `omi-task`, the engineer always runs inside the TASK-006 container, so shell writes outside the worktree are blocked by the OS rather than by prompts. Design and limits: docs/spikes/docker.md.

## Acceptance criteria
- [ ] `omi token set` asks for the `claude setup-token` value without echo and stores it in Windows Credential Manager (stdlib `ctypes` CredWrite/CredRead; no new dependency). On other OSes it says to use the `CLAUDE_CODE_OAUTH_TOKEN` env var instead.
- [ ] `omi worker <wt> <task-file>` reads the token (Credential Manager, else env var), builds the image if missing, and runs `claude -p` as the engineer in the container. The prompt comes from `.claude/agents/engineer.md` plus the task file path, with the model and effort taken from the agent frontmatter, `--permission-mode bypassPermissions` and stdin from `/dev/null`. The token never appears in argv, logs or files, and the command prints the engineer's final report.
- [ ] If Docker is not running or no token is found, `omi worker` stops with a one-line message and changes nothing. There is no fallback to running on the host (PO decision).
- [ ] The engineer no longer commits. After `omi worker`, the Coordinator checks the diff (`git -C <wt> status`/`diff`; it refuses changes to `.gitattributes`, `.gitmodules` or `.git*` unless they are in scope), then commits on the host.
- [ ] The `omi-task` skill (template and root copies kept identical) uses `omi worker` instead of spawning the `engineer` agent; the reviewer stays a host subagent.
- [ ] `docker/` moves into the template so `omi init` installs it. The default image has Node and Python 3, with `@anthropic-ai/claude-code` pinned.
- [ ] Tests cover the argv built by `omi worker` (no token in it), the stop path when Docker or the token is missing, and the Credential Manager wrapper with ctypes stubbed.

## Checkpoint
Done: all 7 criteria. `omi token set` (ctypes CredWriteW/CredReadW, target `omi/CLAUDE_CODE_OAUTH_TOKEN`; live round trip on Windows OK). `omi worker <wt> <task> [--model --effort]` builds `omi-worker:<sha12 of Dockerfile>` if missing, runs `claude -p` with the run.sh flags (run.sh deleted, `worker_argv` replaces it), lists `OUT OF SCOPE` paths after the run (exit 3). `omi worker <wt> --prove` runs prove.sh with the real argv: all PASS live on Windows. docker/ moved to the template (+python3). Skill, engineer.md, AGENTS.md, README updated (root and template copies identical).
Not done: live `claude -p` run in the container (no token here).
Tests: `python tests/test_omi.py` ok (new: test_worker, test_credential_manager, test_template_docker).
Next: PO live run of `omi worker` on a small task. Open: `--setting-sources user` skips project hooks/settings in the container (guard cannot run there) - confirm CLAUDE.md/AGENTS.md is not needed by the engineer; docs/spikes/docker.md still mentions run.sh (outside scope); main checkout docker/ is preferred over the template copy, so this repo uses the old Dockerfile until development has the move.

Fix round 1 done: out_of_scope flags any path component starting with .git (unless exact scope entry) and symlinks (os.path.islink); `omi worker <wt> --model x` now gives usage error. Tests ok (python tests/test_omi.py).
