#!/bin/sh
# post-run hook: runs in the Docker worker (cwd = worktree, no network, no token). Non-zero exit blocks the move to review.
if [ -f go.mod ] && command -v go >/dev/null 2>&1; then exec go test ./...
elif [ -f package.json ] && grep -q '"test"' package.json && command -v npm >/dev/null 2>&1; then exec npm test
elif ls tests/test_*.py test_*.py >/dev/null 2>&1 && python3 -c 'import pytest' >/dev/null 2>&1; then exec python3 -m pytest -q
fi
echo "post-run: no tests found, nothing to run"
