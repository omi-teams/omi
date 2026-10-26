#!/bin/sh
# post-run hook: runs in the Docker worker (cwd = worktree, no network, no token). Non-zero exit blocks the move to review.
need() { command -v "$1" >/dev/null 2>&1 || { echo "post-run: $1 not in the worker image; add it to docker/Dockerfile"; exit 1; }; }
if [ -f go.mod ]; then need go; exec go test ./...
elif [ -f package.json ] && grep -q '"test"' package.json; then need npm; exec npm test
elif ls tests/test_*.py test_*.py >/dev/null 2>&1; then
  python3 -c 'import pytest' >/dev/null 2>&1 || { echo "post-run: pytest not in the worker image; add it to docker/Dockerfile"; exit 1; }
  exec python3 -m pytest -q
fi
echo "post-run: no tests found, nothing to run"
