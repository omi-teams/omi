"""Task scope enforcement: the omi guard hook and the out-of-scope check."""

import json
import os
import re
import subprocess
import sys
import tempfile
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath

from ..common import core
from . import structure
from ..state import resolve as state


def task_scope(wt, tid):
    """Scope globs from detached state or development; the agent-writable worktree copy is ignored."""
    return core.split(core.parse(state.task_text(state.resolve(wt), wt, tid) or "").get("scope"))


GIT_HINT = ".git* paths need an exact scope entry (no globs), e.g. .github/workflows/ci.yml"


def git_hint(paths):
    return GIT_HINT if any(c.lower().startswith(".git") for p in paths for c in str(p).split("/")) else ""


def guard(stdin=None):
    try:
        return _guard(stdin)
    except state.StateError as exc:
        print(f"OMI: omi state registry is invalid ({exc}); fix ~/.omi/state before editing.", file=sys.stderr)
        return 2


def _guard(stdin=None):
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
    session_top = core.git(data.get("cwd", "."), "rev-parse", "--show-toplevel")
    session_root = Path(session_top).resolve() if session_top else None
    omi_session = False
    for repo in dict.fromkeys(p for p in (root, session_root) if p is not None):
        in_repo = (repo / ".omi").is_dir()
        try:
            project = state.resolve(repo)
        except state.StateError as exc:
            if in_repo or engineer:
                raise  # fail closed: guard() blocks with the registry message
            print(f"OMI: warning: cannot read omi state for {repo} ({exc}); guard skipped.", file=sys.stderr)
            continue
        omi_session = omi_session or in_repo or project.detached or (project.code / ".omi").is_dir()
    if not engineer and not omi_session:
        return 0
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
        # Scope comes from state or development, never the agent-writable task copy.
        project = state.resolve(root)
        shown = state.task_text(project, root, tid)
        task_file = state.task_file(project, tid)
        if shown is None:
            reason = f"cannot be checked: {tid} is not on development yet. Stop and report to the Coordinator."
        elif rel and task_file.exists() and (
                (not project.detached and rel == PurePosixPath(f".omi/tasks/{tid}.md"))
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


def changed_paths(wt, committed=False):
    """Changed paths in wt (and untracked ones); committed: also the branch's commits."""
    r = subprocess.run(["git", "-C", str(wt), "status", "--porcelain", "-z", "-uall", "--no-renames"],
                       capture_output=True, encoding="utf-8", errors="replace")
    entries = [e for e in r.stdout.split("\0") if e]
    paths = [e[3:] for e in entries]
    untracked = {e[3:] for e in entries if e[:2] in ("??", "!!")}
    if committed:
        d = subprocess.run(["git", "-C", str(wt), "diff", "--name-only", "-z", "--no-renames", "development...HEAD"],
                           capture_output=True, encoding="utf-8", errors="replace")
        paths += [p for p in d.stdout.split("\0") if p and p not in paths]
    return paths, untracked


def config(project, key, default):
    """`key` from .omi/config.json under the project's state (or under a root path), else `default`."""
    try:
        return json.loads((Path(getattr(project, "state", project)) / ".omi" / "config.json").read_text(encoding="utf-8")).get(key, default)
    except (OSError, ValueError, AttributeError):
        return default


def owned(scope_value, common):
    """The task's scope globs that are not `shared`: the ones that may block a parallel run."""
    return [g for g in core.split(scope_value) if g not in common and not any(PurePosixPath(g).full_match(s) for s in common)]


def plan_error(tid, bad):
    return (f"{tid}: File plan lines the build would ignore (format `- edit|create <path> (<layer>): <note>`):\n"
            + "\n".join(bad) + "\nNothing changed.")


def generated(project):
    """`generated` globs: files `regenerate` rebuilds after a rebase; any task may write them and they never block a parallel run."""
    return [g for g in config(project, "generated", []) if isinstance(g, str) and g]


def shared(project):
    """Globs whose overlap does not block a parallel run: `generated` plus `parallel_shared` (e.g. tests/**; a real clash shows at the rebase)."""
    return [*generated(project), *(g for g in config(project, "parallel_shared", []) if isinstance(g, str) and g)]


def module_tests(globs):
    """`tests/test_<name>.py` for every scoped file `<dir>/<name>.py`: a change's own tests need no NEEDS SCOPE round."""
    return [f"tests/test_{PurePosixPath(g).stem}.py" for g in globs
            if g.endswith(".py") and not g.startswith("tests/") and not any(c in g for c in "*?[")]


def out_of_scope(wt, tid, committed=False):
    """Changed paths in wt that the authoritative task scope does not allow; committed: also the branch's commits."""
    project = state.resolve(wt)
    globs = task_scope(wt, tid)
    globs = [*globs, *generated(project), *module_tests(globs)]
    paths, untracked = changed_paths(wt, committed)
    def bad(p):
        if not project.detached and p == f".omi/tasks/{tid}.md":
            return False
        if os.path.islink(Path(wt) / p):  # host tools could follow it out of the worktree
            return True
        if any(c.lower().startswith(".git") or re.fullmatch(r"(?i)git[^~/]*~\d+(\.[^/]*)?", c) for c in p.split("/")) and p not in globs:
            return True  # .gitattributes, .githooks..., and their Windows 8.3 names (GIT~1): host git processes them; only an exact scope entry allows
        if not committed and p in untracked and p.startswith(".omi-cache/"):
            return False
        return not any(PurePosixPath(p).full_match(g) for g in globs)
    return [p for p in paths if bad(p)]


PLAN_LINE = r"^\s*- (?:edit|create) `?([^\s`{}]+)`?(?: \([^()]*\))?(?:\s*:.*)?\s*$"


def plan_section(text):
    m = re.search(r"^## File plan[ \t]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else None


def file_plan(text):
    """Paths of the `- edit|create <path> (<layer>)[: note]` lines under `## File plan`; None when the task has no such section."""
    body = plan_section(text)
    return None if body is None else {x.group(1) for x in re.finditer(PLAN_LINE, body, re.M)}


def plan_line_errors(text):
    """Every `- edit|create ...` line under `## File plan` that file_plan would not read (one path per line, no `{a,b}`)."""
    body = plan_section(text) or ""
    return [line.strip() for line in body.splitlines()
            if re.match(r"^\s*- (?:edit|create)\b", line) and not re.match(PLAN_LINE, line)]


def plan_violations(wt, tid):
    """`OUT OF PLAN:` / `UNMAPPED:` lines for changed files; plan and map come from state/development, never the worktree."""
    project = state.resolve(wt)
    plan = file_plan(state.task_text(project, wt, tid) or "")
    if plan is None:
        return []
    with tempfile.TemporaryDirectory() as tmp:
        if project.detached:
            text = core.read_task(project.state / structure.MAP) if (project.state / structure.MAP).exists() else None
        else:
            text = core.git(wt, "show", f"development:{structure.MAP}")
        try:
            if text is None:
                raise structure.StructureError(f"{structure.MAP}: not found on development/state")
            (Path(tmp) / ".omi").mkdir()
            (Path(tmp) / structure.MAP).write_text(text, encoding="utf-8", newline="\n")
            rules = structure.load(tmp)
        except structure.StructureError as exc:
            return [f"UNMAPPED: {exc}"]
    out = []
    for p in changed_paths(wt)[0]:
        if p == f".omi/tasks/{tid}.md" or p.startswith(".omi-cache/"):
            continue
        if p not in plan:
            out.append(f"OUT OF PLAN: {p}")
        if not structure.match(rules, p):
            out.append(f"UNMAPPED: {p}")
    return out


def require_scope(tid: str, text: str) -> None:
    """Refuse a write operation without a declared task scope."""
    if not core.split(core.parse(text).get("scope")):
        sys.exit(f"{tid} has no scope; set scope before starting a write role. Nothing changed.")


def glob_prefix(glob: str) -> str:
    return re.split(r"[*?\[]", glob, 1)[0]


def globs_overlap(a: str, b: str) -> bool:
    """# ponytail: compares only the literal prefix before the first wildcard; may report a false overlap, never misses one."""
    for x, y in ((a, b), (b, a)):
        px, py = glob_prefix(x), glob_prefix(y)
        if px == py or (px.startswith(py) and (py != y or py.endswith("/") or px[len(py)] == "/")):
            return True
    return False
