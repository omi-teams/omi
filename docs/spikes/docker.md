# Spike: Docker worker write boundary (TASK-006)

**Recommendation: pending live auth check.** The write boundary is proven; running `claude` with the subscription token is not yet tested.

## Files
- `docker/Dockerfile`: `node:24-slim` (pinned by tag), Claude Code CLI pinned to `2.1.302` (same as host) and installed at build time (baked in, not on a tmpfs, so no exit 126), runs as `node`.
- `docker/run.sh <worktree> [cmd...]`: runs the container, default cmd `claude`. Token goes in via `-e CLAUDE_CODE_OAUTH_TOKEN` (name only, value read from the host env; never on the command line, never in the image or git).
- `docker/prove.sh`: boundary checks; run with `MSYS_NO_PATHCONV=1 docker/run.sh <worktree> sh docker/prove.sh` (Git Bash on Windows).
- Hardening flags: `--user node --read-only --cap-drop ALL --security-opt no-new-privileges`, `/tmp` and `/home/node` as noexec tmpfs, only `-v <worktree>:/work` mounted, plus a nested read-only bind `-v <worktree>/.git:/work/.git:ro`, no Docker socket. `run.sh` sets `MSYS_NO_PATHCONV=1` itself. Everything is labeled `omi-spike=1`.

## Results (Docker Desktop 29.8.1, WSL2)
All PASS: write in `/work` succeeds; writes to `/`, `/usr`, `/work/../x`, `/proc/sys` fail; `mount` fails; exec from `/tmp` fails (noexec); no `/var/run/docker.sock`; uid 1000, `CapEff=0`, `NoNewPrivs=1`; rootfs `ro`, only `/work` is rw (plus the tmpfs).
Caveat: "write to main checkout" and "host `.git` common dir" fail because those paths are not mounted at all (they do not exist in the container). That is the intended design, but it is absence, not a permission denial.

## Commits
The worktree's `.git` is a file pointing at the host path `<main>/.git/worktrees/<id>`. That path is not mounted, so `git` inside the container fails. Decision: **the container only edits files; the Coordinator (or the host-side runner) runs `git add/commit/push` on the host after the run.** The worktree's `.git` file lives inside the rw `/work` mount, so it is re-mounted read-only (`/work/.git:ro`); `prove.sh` checks that overwriting it fails (PASS). Without this, a worker could write a hostile `gitdir:` (hooks, `core.fsmonitor`) that runs code on the host when the Coordinator runs git. The host `.git` dir is not mounted at all. Cost: the worker cannot run `git diff/status`; it may use plain file tools and tests.

## Cost
- Image 758 MB; first build about 29 s (npm install).
- Startup: `docker run --rm ... sh -c true` about 0.9 s total wall time through `run.sh`; `claude --version` about 0.7 s.
- RAM: idle container 0.4 MiB; the `claude` process under load was not measured (needs the live check; read it with `docker stats`).

## Pitfalls handled
noexec tmpfs / exit 126: CLI lives in the image rootfs. Codex auth copy (`last_refresh`) is not relevant as only Claude is tested here; if Codex is added, copy the whole auth file unchanged. Claude config/state lives in the tmpfs `$HOME` and is lost after each run (fine, token is passed fresh).
Terms of use for automated subscription use were not checked yet (see task checkpoint); the PO should confirm.

## PO steps for the live check (Windows PowerShell 5.1)
Run from the repo root of this branch; `<wt>` is the worktree path. `run.sh` needs `sh` (Git for Windows).
```powershell
# 1. Get a token: run `claude setup-token` in a terminal, copy the printed token.
# 2. Read it without echo or history; it lives only in this session's env.
$s = Read-Host -AsSecureString "token"
$env:CLAUDE_CODE_OAUTH_TOKEN = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
# 3. Build
docker build -t omi-spike-worker:1 docker
# 4. Run
& "C:\Program Files\Git\bin\sh.exe" docker/run.sh <wt> claude -p "create hello.txt containing hi, then try to write /etc/x" --permission-mode bypassPermissions
# 5. Clear the token
Remove-Item Env:CLAUDE_CODE_OAUTH_TOKEN; Remove-Variable s
```
Expect: `hello.txt` appears in `<wt>`, the write to `/etc/x` fails (read-only rootfs). If auth works and this holds, go.

Why `bypassPermissions`: headless `-p` has no one to approve Write/Bash, so without it they are denied and the test gives a false no-go. It is acceptable here because the container is the boundary (only `/work` writable, no caps, no socket), not Claude's permission prompts.

Token exposure: the token is visible to the worker's own process env and in `docker inspect` while the container runs (the host user can read it; so can anything inside the container). Use a short-lived token and revoke it if in doubt.

Cleanup: containers use `--rm` and vanish on exit, nothing to remove. Remove the image: `docker rmi omi-spike-worker:1` (label `omi-spike=1`). Optional leftover check, safe when empty: `docker ps -a --filter label=omi-spike=1`.
