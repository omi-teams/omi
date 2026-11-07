"""Register code repositories in detached project state."""

import json
import re
import shutil
import subprocess
from pathlib import Path

from ..common import core
from ..state import resolve as state, sync as state_sync
from . import upgrade


def warn_in_repo_files(code: Path) -> None:
    """Report tracked local omi files ignored by detached state, without changing them."""
    tracked = (core.git(code, "ls-files", "-z", "--", ".omi", "AGENTS.md", ".claude") or "").split("\0")
    roots = {name.split("/", 1)[0] for name in tracked}
    paths = [path for path in (".omi/", "AGENTS.md", ".claude/")
             if path.rstrip("/") in roots]
    if paths:
        print("WARN: in-repo omi files ignored (detached): " + ", ".join(paths))


def attach(rest: list[str]) -> None:
    """Register a checkout using portable origin identity; write only to the state repo."""
    args = list(rest)
    remote_state = None
    if "--state" in args:
        index = args.index("--state")
        if index + 1 == len(args) or args[index + 1].startswith("-"):
            raise state.StateError("usage: omi attach [<repo path>] [--state <git url>]")
        remote_state = args[index + 1]
        del args[index:index + 2]
    if len(args) > 1 or any(arg.startswith("-") for arg in args):
        raise state.StateError("usage: omi attach [<repo path>] [--state <git url>]")
    target = Path(args[0] if args else ".").resolve()
    top = core.git(target, "rev-parse", "--show-toplevel")
    if not top:
        raise state.StateError(f"{target} is not a git repo")
    code = core.main_checkout(top) or Path(top)
    remote = core.git(code, "remote", "get-url", "origin")
    if not remote:
        raise state.StateError(f"{code} has no origin remote")
    home = state.state_home()
    if home.is_relative_to(Path(top).resolve()) or home.is_relative_to(code.resolve()):
        raise state.StateError(f"state directory {home} must be outside the code repo")
    projects = state.registry()
    try:
        identity = state.normalise_url(remote)
    except ValueError as exc:
        raise state.StateError(f"invalid origin in {code}: {remote}: {exc}") from exc
    name = identity.rsplit("/", 1)[-1]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name):
        raise state.StateError(f"invalid project name from origin {remote}")
    project = home / "projects" / name
    if not project.resolve().is_relative_to(home):
        raise state.StateError(f"project directory escapes state repo: {project}")

    def checked_git(*args: str) -> None:
        result = subprocess.run(["git", *args], capture_output=True, encoding="utf-8", errors="replace")
        if result.returncode:
            raise state.StateError(f"git {args[0]} failed: {result.stderr.strip()}")

    def prepare_development() -> None:
        if (not core.git(code, "show-ref", "--verify", "refs/heads/development")
                and core.git(code, "show-ref", "--verify", "refs/remotes/origin/development")):
            checked_git("-C", str(code), "branch", "--track", "development", "origin/development")
            print("created development tracking origin/development")

    if identity in projects:
        print(f"already attached: {projects[identity]}")
        warn_in_repo_files(code)
        prepare_development()
        return
    if project.exists() or project.is_symlink():
        raise state.StateError(f"project already exists: {project}; origin differs or project.json is missing")

    if not home.exists():
        home.parent.mkdir(parents=True, exist_ok=True)
        if remote_state:
            checked_git("clone", "--", remote_state, str(home))
        else:
            checked_git("init", "-q", "-b", "main", str(home))
    elif remote_state:
        raise state.StateError(f"state directory already exists: {home}; omit --state")
    elif not (home / ".git").exists():
        if core.git(home, "rev-parse", "--show-toplevel"):
            raise state.StateError(f"state directory {home} belongs to another git repo")
        checked_git("init", "-q", "-b", "main", str(home))
    if Path(core.git(home, "rev-parse", "--show-toplevel") or "").resolve() != home:
        raise state.StateError(f"{home} is not a state git repo")
    # A cloned registry may already contain this origin or a conflicting project name.
    projects = state.registry()
    if identity in projects:
        print(f"already attached: {projects[identity]}")
        warn_in_repo_files(code)
        prepare_development()
        return
    if project.exists() or project.is_symlink():
        raise state.StateError(f"project already exists: {project}; origin differs or project.json is missing")
    if not project.resolve().is_relative_to(home):
        raise state.StateError(f"project directory escapes state repo: {project}")
    rel = project.relative_to(home).as_posix()
    attrs = home / ".gitattributes"
    new_attrs = not attrs.exists()
    try:
        if new_attrs:
            core.write_text(attrs, "* text=auto eol=lf\n")
        upgrade.init(project, detached=True)
        (project / "project.json").write_text(json.dumps({"remote": remote}, indent=2) + "\n", encoding="utf-8", newline="\n")
        paths = [rel, ".gitattributes"] if new_attrs else [rel]
        checked_git("-C", str(home), "add", "--", *paths)
        checked_git("-C", str(home), "commit", "--only", "-m", f"omi: attach {name}", "--", *paths)
    except Exception:
        subprocess.run(["git", "-C", str(home), "rm", "--cached", "-r", "-f", "--ignore-unmatch", "--", rel,
                        *([".gitattributes"] if new_attrs else [])],
                       capture_output=True)
        if project.exists():
            shutil.rmtree(project)
        if new_attrs:
            attrs.unlink(missing_ok=True)
        raise
    print(f"attached: {project}")
    warn_in_repo_files(code)
    if core.git(home, "remote"):
        state_sync.push(state.Project(project, code, True))
    else:
        print(f'private remote: git -C "{home}" remote add origin <private-git-url>')
    prepare_development()


