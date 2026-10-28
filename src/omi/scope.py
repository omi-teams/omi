"""Task scope enforcement: the omi guard hook and the out-of-scope check."""

import json
import os
import re
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath

from . import core


def task_scope(wt, tid):
    """Scope globs of a task, read from the task file on development; the worktree copy is agent-writable and ignored."""
    return core.split(core.parse(core.git(wt, "show", f"development:.omi/tasks/{tid}.md") or "").get("scope"))


GIT_HINT = ".git* paths need an exact scope entry (no globs), e.g. .github/workflows/ci.yml"


def git_hint(paths):
    return GIT_HINT if any(c.lower().startswith(".git") for p in paths for c in str(p).split("/")) else ""


def guard(stdin=None):
    data = json.loads((stdin or sys.stdin.buffer).read())
    tool_input = data.get("tool_input", {})
    raw = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not raw:
        return 0
    path = Path(raw)
    if not path.is_absolute():
        path = Path(data.get("cwd", ".")) / path
    d = path.parent
    while not d.exists() and d != d.parent:
        d = d.parent
    engineer = data.get("agent_type") == "omi-agent-engineer"  # subagents share the session cwd; only the payload tells
    top = core.git(d, "rev-parse", "--show-toplevel")
    root = Path(top).resolve() if top else None
    branch = (core.git(d, "rev-parse", "--abbrev-ref", "HEAD") or "") if top else ""
    try:
        rel = PurePosixPath(path.resolve().relative_to(root).as_posix())
    except (ValueError, TypeError):
        rel = None
    if path.parent.name.lower() == ".claude" and fnmatch(path.name.lower(), "settings*.json") and not (
            branch.startswith("task/") and rel):
        print(f"OMI: {path} is Claude Code config; only a task whose scope names it may change it.", file=sys.stderr)
        return 2
    if not top:
        reason = "is outside the task worktree."
        if not engineer:
            return 0  # not inside a project
    elif branch.startswith("task/"):
        tid = branch[5:]
        # scope comes from development: the worktree copy is agent-writable, so it can't be trusted
        shown = core.git(root, "show", f"development:.omi/tasks/{tid}.md")
        task_file = root / ".omi" / "tasks" / f"{tid}.md"
        if shown is None:
            reason = f"cannot be checked: {tid} is not on development yet. Stop and report to the Coordinator."
        elif rel and task_file.exists() and (
                rel == PurePosixPath(f".omi/tasks/{tid}.md")
                or any(rel.full_match(g) for g in core.split(core.parse(shown).get("scope")))):
            return 0
        else:
            reason = f"is outside the scope of {tid}. Stop and report NEEDS SCOPE to the Coordinator."
            if git_hint([rel or path]):
                reason += f" {GIT_HINT}."
    elif engineer:
        reason = "is outside the task worktree."
    else:
        # main checkout: while a task runs, product code changes belong in its worktree
        active = core.task_worktrees(root)
        if not active or (rel and rel.parts[:1] in (("docs",), (".omi",))):
            return 0
        reason = f"is product code; {', '.join(active)} is running, write inside its worktree."
    print(f"OMI: {rel or path} {reason}", file=sys.stderr)
    return 2


def out_of_scope(wt, tid, committed=False):
    """Changed paths in wt that the task's scope (read from development) does not allow; committed: also the branch's commits."""
    globs = task_scope(wt, tid)
    r = subprocess.run(["git", "-C", str(wt), "status", "--porcelain", "-z", "-uall", "--no-renames"],
                       capture_output=True, encoding="utf-8", errors="replace")
    entries = [e for e in r.stdout.split("\0") if e]
    paths = [e[3:] for e in entries]
    untracked = {e[3:] for e in entries if e[:2] in ("??", "!!")}
    if committed:
        d = subprocess.run(["git", "-C", str(wt), "diff", "--name-only", "-z", "--no-renames", "development...HEAD"],
                           capture_output=True, encoding="utf-8", errors="replace")
        paths += [p for p in d.stdout.split("\0") if p and p not in paths]
    def bad(p):
        if p == f".omi/tasks/{tid}.md":
            return False
        if os.path.islink(Path(wt) / p):  # host tools could follow it out of the worktree
            return True
        if any(c.lower().startswith(".git") or re.fullmatch(r"(?i)git[^~/]*~\d+(\.[^/]*)?", c) for c in p.split("/")) and p not in globs:
            return True  # .gitattributes, .githooks..., and their Windows 8.3 names (GIT~1): host git processes them; only an exact scope entry allows
        if not committed and p in untracked and p.startswith(".omi-cache/"):
            return False
        return not any(PurePosixPath(p).full_match(g) for g in globs)
    return [p for p in paths if bad(p)]
