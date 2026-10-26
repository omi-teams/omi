#!/bin/sh
# post-run hook: runs in the Docker worker (cwd = worktree, no network, no token). Non-zero exit blocks the move to review.
need() { command -v "$1" >/dev/null 2>&1 || { echo "post-run: $1 not in the worker image; add it to docker/Dockerfile"; exit 1; }; }
has_test_script() { while IFS= read -r l || [ -n "$l" ]; do case $l in *'"test"'*) return 0;; esac; done < package.json; return 1; }
cfg_test() { [ -f .omi/config.json ] && python3 -c 'import json;print(json.load(open(".omi/config.json",encoding="utf-8")).get("test") or "")' 2>/dev/null; }
t=$(cfg_test)
[ -n "$t" ] && exec sh -c "$t"
found=
for f in tests/test_*.py test_*.py; do [ -f "$f" ] && found=1; done
if [ -f go.mod ]; then need go; exec go test ./...
elif [ -f package.json ] && has_test_script; then need npm; exec npm test
elif [ -n "$found" ]; then
  python3 -c 'import pytest' >/dev/null 2>&1 || { echo "post-run: pytest not in the worker image; add it to docker/Dockerfile"; exit 1; }
  exec python3 -m pytest -q
fi
echo "post-run: no tests found, nothing to run"
