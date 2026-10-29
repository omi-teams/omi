"""Git transport and command-scoped commits for detached state."""

import hashlib
import subprocess
from pathlib import Path

from . import core, state


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    """Run state git with bounded network waits and useful errors."""
    try:
        return subprocess.run(["git", "--literal-pathspecs", "-C", str(root), *args], capture_output=True,
                              encoding="utf-8", errors="replace", timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise state.StateError(f"state git {args[0]} failed: {exc}") from exc


def repo(project: state.Project) -> Path:
    """Return the shared state repository containing this project."""
    return Path(core.git(project.state, "rev-parse", "--show-toplevel") or state.state_home())


def conflicts(root: Path) -> None:
    """Stop before further writes when a merge or rebase needs human resolution."""
    result = git(root, "diff", "--name-only", "--diff-filter=U")
    if result.returncode:
        raise state.StateError(result.stderr.strip())
    if result.stdout.strip():
        raise state.StateError("state rebase conflict: " + ", ".join(result.stdout.splitlines()))
    for name in ("rebase-merge", "rebase-apply"):
        path = git(root, "rev-parse", "--git-path", name).stdout.strip()
        if path and (root / path).exists():
            raise state.StateError("state rebase in progress; resolve it before omi sync")


def pull(project: state.Project) -> bool:
    """Refresh state, allowing offline status and preserving conflict information."""
    root = repo(project)
    conflicts(root)
    if not core.git(root, "remote"):
        print("state pull skipped: no remote")
        return False
    try:
        upstream = core.git(root, "rev-parse", "--abbrev-ref", "@{upstream}")
        extra = [] if upstream else [(core.git(root, "remote") or "").splitlines()[0],
                                     core.git(root, "rev-parse", "--abbrev-ref", "HEAD") or "HEAD"]
        result = git(root, "pull", "--rebase", "--autostash", *extra)
    except state.StateError:
        print("state pull skipped: offline or remote unavailable")
        return False
    conflicts(root)
    if result.returncode:
        print("state pull skipped: offline or remote unavailable (check remote/upstream)")
        return False
    return True


def snapshot(project: state.Project) -> dict[str, bytes]:
    """Fingerprint tracked and unignored files without including unrelated projects."""
    root = repo(project)
    result = git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--",
                 project.state.relative_to(root).as_posix())
    if result.returncode:
        raise state.StateError(result.stderr.strip())
    return {name: hashlib.sha256((root / name).read_bytes()).digest()
            for name in result.stdout.split("\0") if name and (root / name).is_file()}


def commit(project: state.Project, paths: list[str], what: str) -> None:
    """Commit exactly the selected files, preserving unrelated index entries."""
    if not paths:
        return
    root = repo(project)
    conflicts(root)
    present = [p for p in paths if (root / p).exists() or (root / p).is_symlink()]
    if present:
        result = git(root, "add", "-A", "--", *present)
        if result.returncode:
            raise state.StateError("state commit failed: " + result.stderr.strip())
    result = git(root, "commit", "--only", "-m", f"chore({project.state.name}): {what}", "--", *paths)
    if result.returncode:
        raise state.StateError("state commit failed: " + result.stderr.strip())


def push(project: state.Project) -> bool:
    """Keep local commits and give a recovery command when transport fails."""
    root = repo(project)
    if not core.git(root, "remote"):
        print("state push skipped: no remote")
        return True
    try:
        upstream = core.git(root, "rev-parse", "--abbrev-ref", "@{upstream}")
        remote = (core.git(root, "remote") or "").splitlines()[0]
        result = git(root, "push", *([] if upstream else ["--set-upstream", remote, "HEAD"]))
        if result.returncode == 0:
            return True
    except state.StateError:
        pass
    print("STATE NOT PUSHED: run omi sync")
    return False


def sync(project: state.Project) -> int:
    """Pull, commit remaining changes across the shared state repo, and push."""
    pull(project)
    root = repo(project)
    result = git(root, "ls-files", "-z", "--modified", "--deleted", "--others", "--exclude-standard")
    if result.returncode:
        raise state.StateError(result.stderr.strip())
    paths = sorted(set(filter(None, result.stdout.split("\0"))))
    # Include staged-only changes as well as edits left by the Coordinator.
    staged = git(root, "diff", "--cached", "--name-only", "-z")
    if staged.returncode:
        raise state.StateError(staged.stderr.strip())
    paths = sorted(set(paths) | set(filter(None, staged.stdout.split("\0"))))
    commit(project, paths, "sync state")
    if not push(project):
        return 1
    print("state synced")
    return 0
