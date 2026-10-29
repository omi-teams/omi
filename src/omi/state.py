"""Resolve a code checkout and its optional detached project state."""

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from . import core


@dataclass(frozen=True)
class Project:
    state: Path
    code: Path
    detached: bool = False


def normalise_url(url: str) -> str:
    """Match HTTPS, SSH and scp remotes without changing case-sensitive repo paths."""
    url = url.strip().rstrip("/")
    if "://" in url:
        parsed = urlsplit(url)
        if parsed.hostname:
            return parsed.hostname.lower() + "/" + parsed.path.strip("/").removesuffix(".git")
    match = re.fullmatch(r"(?:[^/@:]+@)?([^/:]+):(.+)", url)
    if match and not re.match(r"^[A-Za-z]:[/\\]", url):
        return match[1].lower() + "/" + match[2].strip("/").removesuffix(".git")
    host, sep, path = url.partition("/")
    return host.lower() + sep + path.removesuffix(".git")


def state_home() -> Path:
    return Path(os.environ.get("OMI_STATE", str(Path.home() / ".omi" / "state"))).expanduser().resolve()


class StateError(ValueError):
    """Invalid detached state or an attach operation that cannot proceed."""


def registry() -> dict[str, Path]:
    """Validate every manifest, including entries unrelated to the current checkout."""
    found = {}
    for manifest in sorted((state_home() / "projects").glob("*/project.json")):
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise StateError(f"invalid project manifest {manifest}: {exc}") from exc
        if not isinstance(data, dict) or not isinstance(data.get("remote"), str) or not data["remote"].strip():
            raise StateError(f"invalid project manifest {manifest}: expected a remote string")
        try:
            remote = normalise_url(data["remote"])
        except ValueError as exc:
            raise StateError(f"invalid project manifest {manifest}: {exc}") from exc
        if remote in found:
            raise StateError(f"multiple detached projects: {found[remote] / 'project.json'} and {manifest}")
        found[remote] = manifest.parent.resolve()
    return found


def resolve(cwd: str | Path | Project = ".") -> Project:
    """One root resolver for commands; ordinary checkouts keep their local state."""
    if isinstance(cwd, Project):
        return cwd
    top = Path(core.git(cwd, "rev-parse", "--show-toplevel") or cwd).resolve()
    code = core.main_checkout(top) or top
    remote = core.git(code, "remote", "get-url", "origin")
    projects = registry()
    try:
        match = projects.get(normalise_url(remote)) if remote else None
    except ValueError as exc:
        raise StateError(f"invalid origin in {code}: {remote}: {exc}") from exc
    return Project(match, code, True) if match else Project(top, code)


def task_file(project: Project, tid: str) -> Path:
    """Detached tasks live in state; in-repo tasks prefer the task worktree."""
    base = project.state / ".omi" / "tasks" / f"{tid}.md"
    if project.detached:
        return base
    wt = core.task_worktrees(project.code).get(tid)
    candidate = Path(wt) / ".omi" / "tasks" / f"{tid}.md" if wt else base
    return candidate if candidate.exists() else base


def task_text(project: Project, wt: str | Path, tid: str) -> str | None:
    """Authoritative scope input, never the agent-writable worktree task."""
    if project.detached:
        task = project.state / ".omi" / "tasks" / f"{tid}.md"
        return task.read_text(encoding="utf-8") if task.exists() else None
    return core.git(wt, "show", f"development:.omi/tasks/{tid}.md")


def catalog_root(project: Project, wt: str | Path) -> Path:
    return project.state if project.detached else Path(wt)
