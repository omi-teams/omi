#!/bin/sh
# post-run hook: runs in the Docker worker (cwd = worktree, no network, no token). Non-zero exit blocks the move to review.
need() { command -v "$1" >/dev/null 2>&1 || { echo "post-run: $1 not in the worker image; add it to docker/Dockerfile"; exit 1; }; }
has_test_script() { while IFS= read -r l || [ -n "$l" ]; do case $l in *'"test"'*) return 0;; esac; done < package.json; return 1; }
cfg_test() { cfg="${OMI_PROJECT_STATE:-.}/.omi/config.json"; [ -f "$cfg" ] && python3 -c 'import json,sys;print(json.load(open(sys.argv[1],encoding="utf-8")).get("test") or "")' "$cfg" 2>/dev/null; }
if [ -f "${OMI_PROJECT_STATE:-.}/.omi/structure.md" ]; then
  # hook container: git needs the main repo's worktree dir (OMI_GIT_DIR); GIT_DIR is set in a subshell, not for the project tests
  ( [ -z "$OMI_GIT_DIR" ] || export GIT_DIR="$OMI_GIT_DIR" GIT_WORK_TREE="$PWD"; python3 -m omi structure check --changed ) || { echo "post-run: structure check failed"; exit 1; }
fi
# new or changed binary files over 1 MB are build outputs: they go to /tmp or /cache, never into the diff
big=$(command -v git >/dev/null 2>&1 && ( [ -z "$OMI_GIT_DIR" ] || export GIT_DIR="$OMI_GIT_DIR" GIT_WORK_TREE="$PWD"
  base=  # committed files: since development, else the merge base with the default branch
  for b in development "$(git symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null)" main master; do
    [ -n "$b" ] && git rev-parse -q --verify "$b^{commit}" >/dev/null 2>&1 && { base=$b; break; }
  done
  [ -n "$base" ] || echo "post-run: binary check could not diff committed files (no development or default branch)" >&2
  [ -z "$base" ] || git diff --name-only "$base"...HEAD 2>/dev/null ||
    echo "post-run: binary check could not diff committed files (no merge base with $base)" >&2
  { git diff --name-only HEAD; git ls-files --others --exclude-standard; } 2>/dev/null ) |
  sort -u | while IFS= read -r f; do
    [ -f "$f" ] && [ "$(wc -c < "$f")" -gt 1048576 ] && ! grep -Iq . "$f" && echo "$f"
  done )
[ -z "$big" ] || { echo "post-run: new or changed binary files over 1 MB (build outputs go to /tmp or /cache):"; echo "$big"; exit 1; }
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
