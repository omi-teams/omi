# Spike: Docker worker write boundary (TASK-006)

**Recommendation: pending live auth check.** The write boundary is proven; running `claude` with the subscription token is not yet tested.

## Files
- `docker/Dockerfile`: `node:24-slim` (pinned by tag), Claude Code CLI installed at build time (baked in, not on a tmpfs, so no exit 126), runs as `node`.
- `docker/run.sh <worktree> [cmd...]`: runs the container, default cmd `claude`. Token goes in via `-e CLAUDE_CODE_OAUTH_TOKEN` (name only, value read from the host env; never on the command line, never in the image or git).
- `docker/prove.sh`: boundary checks; run with `MSYS_NO_PATHCONV=1 docker/run.sh <worktree> sh docker/prove.sh` (Git Bash on Windows).
- Hardening flags: `--user node --read-only --cap-drop ALL --security-opt no-new-privileges`, `/tmp` and `/home/node` as noexec tmpfs, only `-v <worktree>:/work` mounted, no Docker socket. Everything is labeled `omi-spike=1`.

## Results (Docker Desktop 29.8.1, WSL2)
All PASS: write in `/work` succeeds; writes to `/`, `/usr`, `/work/../x`, `/proc/sys` fail; `mount` fails; exec from `/tmp` fails (noexec); no `/var/run/docker.sock`; uid 1000, `CapEff=0`, `NoNewPrivs=1`; rootfs `ro`, only `/work` is rw (plus the tmpfs).
Caveat: "write to main checkout" and "host `.git` common dir" fail because those paths are not mounted at all (they do not exist in the container). That is the intended design, but it is absence, not a permission denial.

## Commits
The worktree's `.git` is a file pointing at the host path `<main>/.git/worktrees/<id>`. That path is not mounted, so `git` inside the container fails. Decision: **the container only edits files; the Coordinator (or the host-side runner) runs `git add/commit/push` on the host after the run.** This keeps the whole `.git` unreachable (no hooks/config tampering). Cost: the worker cannot run `git diff/status`; it may use plain file tools and tests.

## Cost
- Image 758 MB; first build about 29 s (npm install).
- Startup: `docker run --rm ... sh -c true` about 0.9 s total wall time through `run.sh`; `claude --version` about 0.7 s.
- RAM: idle container 0.4 MiB; the `claude` process under load was not measured (needs the live check; read it with `docker stats`).

## Pitfalls handled
noexec tmpfs / exit 126: CLI lives in the image rootfs. Codex auth copy (`last_refresh`) is not relevant as only Claude is tested here; if Codex is added, copy the whole auth file unchanged. Claude config/state lives in the tmpfs `$HOME` and is lost after each run (fine, token is passed fresh).
Terms of use for automated subscription use were not checked yet (see task checkpoint); the PO should confirm.

## PO steps for the live check
1. On the host: `claude setup-token`, copy the printed token.
2. `export CLAUDE_CODE_OAUTH_TOKEN=<token>` (Git Bash; do not put it in a file under git).
3. `docker build -t omi-spike-worker:1 docker`
4. `MSYS_NO_PATHCONV=1 docker/run.sh <worktree-path> claude -p "create hello.txt containing hi, then try to write /etc/x"`
5. Expect: `hello.txt` appears in the worktree, the write to `/etc/x` fails. If auth works and this holds, go.
6. Cleanup: `docker rm -f $(docker ps -aq --filter label=omi-spike=1)`, `docker rmi omi-spike-worker:1`.
