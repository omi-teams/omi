#!/bin/sh
# Usage: docker/run.sh <worktree-path> [cmd...]   (default cmd: claude)
# Token: export CLAUDE_CODE_OAUTH_TOKEN first; passed by name only (-e NAME), never by value.
set -eu
export MSYS_NO_PATHCONV=1  # Git Bash on Windows: stop path mangling of -v and args
WT=$(cd "$1" && pwd); shift
[ $# -gt 0 ] || set -- claude
IMG=${OMI_IMAGE:-omi-spike-worker:1}
# The worktree .git file is re-mounted read-only on top, so a worker cannot plant a hostile gitdir/hooks.
# Only the worktree is mounted rw. Rootfs read-only; /tmp and /home/node are tmpfs (noexec, nosuid).
exec docker run --rm -i --label omi-spike=1 \
  --user node --read-only --cap-drop ALL --security-opt no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,size=256m \
  --tmpfs /home/node:rw,noexec,nosuid,uid=1000,gid=1000,size=256m \
  -e CLAUDE_CODE_OAUTH_TOKEN -e HOME=/home/node \
  -v "$WT:/work" -v "$WT/.git:/work/.git:ro" -w /work "$IMG" "$@"
