#!/bin/sh
# Usage: docker/run.sh <worktree-path> [cmd...]   (default cmd: claude)
# Token: export CLAUDE_CODE_OAUTH_TOKEN first; passed by name only (-e NAME), never by value.
set -eu
WT=$(cd "$1" && pwd); shift
[ $# -gt 0 ] || set -- claude
IMG=${OMI_IMAGE:-omi-spike-worker:1}
# Only the worktree is mounted rw. Rootfs read-only; /tmp and /home/node are tmpfs (noexec, nosuid).
exec docker run --rm -i --label omi-spike=1 \
  --user node --read-only --cap-drop ALL --security-opt no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,size=256m \
  --tmpfs /home/node:rw,noexec,nosuid,uid=1000,gid=1000,size=256m \
  -e CLAUDE_CODE_OAUTH_TOKEN -e HOME=/home/node \
  -v "$WT:/work" -w /work "$IMG" "$@"
