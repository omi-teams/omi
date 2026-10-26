#!/bin/sh
# post-run hook: runs in the Docker worker (cwd = worktree, no network, no token). Non-zero exit blocks the move to review.
exec python3 tests/test_omi.py
