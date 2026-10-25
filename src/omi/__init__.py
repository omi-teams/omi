"""OMI Squad CLI: init, status, guard. Stdlib only."""

import json
import shutil
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath

TEMPLATE = Path(__file__).parent / "template"
TOOLS = ("git", "gh", "docker", "claude", "codex")
STATUSES = ("in-progress", "review", "blocked", "planned")
USAGE = """usage: omi <command>
  init [dir]   install the squad into a project (never overwrites)
  status       show tasks, checkpoints and the next suggested task
  guard        Claude Code PreToolUse hook: block writes outside task scope
  github       set up branches and rulesets: squad merges to development, only the PO to staging/main"""


def git(cwd, *args):
    r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def split(value):
    return [x.strip() for x in (value or "").split(",") if x.strip()]


def meta(path):
    return parse(path.read_text(encoding="utf-8"))


def parse(text):
    """Frontmatter of a task file as a dict, plus the raw text under '_text'."""
    m = {"_text": text}
    if text.startswith("---"):
        for line in text.split("---", 2)[1].splitlines():
            key, sep, value = line.partition(":")
            if sep:
                m[key.strip()] = value.split("#")[0].strip()
    return m


def init(target="."):
    target = Path(target).resolve()
    for src in sorted(TEMPLATE.rglob("*")):
        if src.is_dir():
            continue
        # template stores dot-dirs as dot-xxx so packaging doesn't drop them
        parts = ["." + p[4:] if p.startswith("dot-") else p for p in src.relative_to(TEMPLATE).parts]
        rel = PurePosixPath(*parts)
        dst = target.joinpath(*parts)
        if dst.exists():
            print(f"skip   {rel} (exists)")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        print(f"create {rel}")
    if not (target / ".git").exists():
        subprocess.run(["git", "init", "-q", "-b", "main", str(target)], check=True)
        print("git init (branch main)")
    print("tools: " + ", ".join(f"{t} {'ok' if shutil.which(t) else 'MISSING'}" for t in TOOLS))
    print("next: open Claude Code or Codex here and type omi-idea")


def task_worktrees(root):
    """{task id: worktree path} for every checked-out task/* branch."""
    found = {}
    for block in (git(root, "worktree", "list", "--porcelain") or "").split("\n\n"):
        info = dict(line.split(" ", 1) for line in block.splitlines() if " " in line)
        branch = info.get("branch", "").removeprefix("refs/heads/")
        if branch.startswith("task/"):
            found[branch[5:]] = info["worktree"]
    return found


def tasks(root):
    found = {f.stem: meta(f) for f in sorted((root / ".omi" / "tasks").glob("TASK-*.md"))}
    # a task's live checkpoint is on its branch, in its worktree
    for tid, wt in task_worktrees(root).items():
        f = Path(wt) / ".omi" / "tasks" / f"{tid}.md"
        if f.exists():
            found[tid] = meta(f) | {"worktree": wt}
    return dict(sorted(found.items()))


def checkpoint(text):
    _, sep, rest = text.partition("## Checkpoint")
    return rest.split("\n## ", 1)[0].strip() if sep else ""


def drift(wt, tid):
    """One line: commits ahead of development, dirty flag, stale-checkpoint warning."""
    ahead = git(wt, "rev-list", "--count", "development..HEAD")
    dirty = bool(git(wt, "status", "--porcelain"))
    last = git(wt, "log", "-1", "--format=%H", "--", f".omi/tasks/{tid}.md")
    after = git(wt, "rev-list", "--count", f"{last}..HEAD") if last else ahead
    line = f"ahead of development: {ahead if ahead is not None else '?'}, uncommitted: {'yes' if dirty else 'no'}"
    return line + (" - WARNING checkpoint stale" if after not in (None, "0") else "")


def status(cwd="."):
    root = Path(git(cwd, "rev-parse", "--show-toplevel") or cwd).resolve()
    print(f"branch: {git(root, 'rev-parse', '--abbrev-ref', 'HEAD')}")
    ts = tasks(root)
    if not ts:
        print("no tasks yet - run omi-idea")
        return
    done = {k for k, m in ts.items() if m.get("status") == "done"}
    print(f"done: {len(done)}/{len(ts)}")
    for st in STATUSES:
        for k, m in ts.items():
            if m.get("status", "planned") == st:
                print(f"[{st}] {k} {m.get('title', '')}")
                if st != "planned":
                    if "worktree" in m:
                        print(f"  worktree: {m['worktree']}")
                        print("  " + drift(m["worktree"], k))
                    for line in checkpoint(m["_text"]).splitlines():
                        print(f"  {line}")
    nxt = next((k for k, m in ts.items()
                if m.get("status", "planned") == "planned" and set(split(m.get("depends"))) <= done), None)
    print(f"next: {nxt or 'none ready'}")


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
    engineer = data.get("agent_type") == "engineer"  # subagents share the session cwd; only the payload tells
    top = git(d, "rev-parse", "--show-toplevel")
    root = Path(top).resolve() if top else None
    branch = (git(d, "rev-parse", "--abbrev-ref", "HEAD") or "") if top else ""
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
        shown = git(root, "show", f"development:.omi/tasks/{tid}.md")
        task_file = root / ".omi" / "tasks" / f"{tid}.md"
        if shown is None:
            reason = f"cannot be checked: {tid} is not on development yet. Stop and report to the Coordinator."
        elif rel and task_file.exists() and (
                rel == PurePosixPath(f".omi/tasks/{tid}.md")
                or any(rel.full_match(g) for g in split(parse(shown).get("scope")))):
            return 0
        else:
            reason = f"is outside the scope of {tid}. Stop and report NEEDS SCOPE to the Coordinator."
    elif engineer:
        reason = "is outside the task worktree."
    else:
        # main checkout: while a task runs, product code changes belong in its worktree
        active = task_worktrees(root)
        if not active or (rel and rel.parts[:1] in (("docs",), (".omi",))):
            return 0
        reason = f"is product code; {', '.join(active)} is running, write inside its worktree."
    print(f"OMI: {rel or path} {reason}", file=sys.stderr)
    return 2


def rulesets():
    """{name: payload} of the GitHub rulesets omi github applies."""
    def ruleset(name, refs, rules, bypass, target="branch"):
        kind = "heads" if target == "branch" else "tags"
        return {"name": name, "target": target, "enforcement": "active", "bypass_actors": bypass,
                "conditions": {"ref_name": {"include": [f"refs/{kind}/{r}" for r in refs], "exclude": []}},
                "rules": [{"type": t, **({"parameters": p} if p else {})} for t, p in rules]}
    admin = [{"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always"}]
    pr = {"required_approving_review_count": 0, "dismiss_stale_reviews_on_push": False,
          "require_code_owner_review": False, "require_last_push_approval": False,
          "required_review_thread_resolution": False}
    checks = {"required_status_checks": [{"context": "test"}], "strict_required_status_checks_policy": False}
    return {r["name"]: r for r in (
        ruleset("omi-development", ["development"], [("deletion", None), ("non_fast_forward", None)], []),
        ruleset("omi-po-only", ["staging", "main"],
                [("deletion", None), ("non_fast_forward", None), ("update", None),
                 ("pull_request", pr), ("required_status_checks", checks)], admin),
        # creating rc-* tags stays allowed (omi-release); moving or deleting them is admin only
        ruleset("omi-tags", ["rc-*", "v*"], [("update", None), ("deletion", None)], admin, "tag"))}


def gh(*args, body=None):
    r = subprocess.run(["gh", "api", *args, *(["--input", "-"] if body else [])],
                       input=json.dumps(body) if body else None, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"gh api {' '.join(args)} failed: {r.stderr.strip() or r.stdout.strip()}")
    return json.loads(r.stdout) if r.stdout.strip() else None


def same(live, want):
    """True if live holds everything we send (GitHub adds extra fields); lists compare in any order."""
    if isinstance(want, dict):
        return isinstance(live, dict) and all(k in live and same(live[k], v) for k, v in want.items())
    if isinstance(want, list):
        return isinstance(live, list) and len(live) == len(want) and all(
            any(same(l, w) for l in live) for w in want)
    return live == want


def accounts():
    """(logins, active) from local gh state (no network); None if gh cannot tell."""
    r = subprocess.run(["gh", "auth", "status", "--json", "hosts"], capture_output=True, text=True)
    try:
        hs = json.loads(r.stdout)["hosts"].get("github.com", [])
    except (ValueError, KeyError):
        return None
    if r.returncode and hs:
        return None
    return [h["login"] for h in hs], next((h["login"] for h in hs if h.get("active")), "")


def github(po=False):
    if not shutil.which("gh"):
        sys.exit("gh is not installed (https://cli.github.com); omi github needs it.")
    if not po:
        return apply_github()
    before = accounts()
    prev = before[1] if before else ""
    if not prev:
        sys.exit("no active squad gh account (or gh auth status failed); log in as the squad account first. Nothing changed.")
    try:
        r = subprocess.run(["gh", "auth", "login", "--web", "-h", "github.com"])
        now = accounts()
        if r.returncode:
            sys.exit("gh auth login failed; cleaning up.")
        if now is None:
            sys.exit("cannot read gh accounts after login; cleaning up.")
        if not set(now[0]) - set(before[0]) and now[1] == prev:
            sys.exit(f"logged in as {prev}, the same as the squad account; the PO must log in with their own account. Nothing changed.")
        apply_github()
    finally:
        left = []
        try:
            cur = accounts()
            for u in (set(cur[0]) - set(before[0])) if cur else ():
                try:
                    subprocess.run(["gh", "auth", "logout", "-h", "github.com", "-u", u])
                except BaseException:  # keep going: the switch below must still run
                    pass
        finally:
            try:
                subprocess.run(["gh", "auth", "switch", "-h", "github.com", "-u", prev])
            finally:
                cur = accounts()
                left = sorted(set(cur[0]) - set(before[0])) if cur else ["(unknown: gh auth status failed)"]
                if left:
                    sys.exit(f"WARNING: PO credentials may still be stored in gh: {left}. Run `gh auth logout -u <login>` now, then `gh auth switch -u {prev}`.")
                print(f"active gh account: {cur[1]}")


def apply_github():
    r = subprocess.run(["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"cannot read repo from gh: {r.stderr.strip()}")
    repo = r.stdout.strip()
    if not gh(f"repos/{repo}")["permissions"]["admin"]:
        sys.exit(f"the gh token has no admin on {repo}; nothing changed. Use an admin token.")
    try:
        gh(f"repos/{repo}/git/ref/heads/staging")
        print("ok     branch staging exists")
    except SystemExit:  # ponytail: any lookup failure counts as missing; POST then reports a real error
        sha = gh(f"repos/{repo}/git/ref/heads/main")["object"]["sha"]
        gh("-X", "POST", f"repos/{repo}/git/refs", body={"ref": "refs/heads/staging", "sha": sha})
        print("create branch staging (from main)")
    existing = {x["name"]: x["id"] for x in gh(f"repos/{repo}/rulesets")}
    for name, payload in rulesets().items():
        if name in existing:
            if same(gh(f"repos/{repo}/rulesets/{existing[name]}"), {k: v for k, v in payload.items() if k != "name"}):
                print(f"unchanged ruleset {name}")
                continue
            gh("-X", "PUT", f"repos/{repo}/rulesets/{existing[name]}", body=payload)
            print(f"update ruleset {name}")
        else:
            gh("-X", "POST", f"repos/{repo}/rulesets", body=payload)
            print(f"create ruleset {name}")
    print("WARNING: admins bypass the staging/main rule. If the squad uses an admin account, set it back to Write.")


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:] if argv is None else argv
    cmd, rest = (args[0], args[1:]) if args else ("help", [])
    if cmd == "init":
        init(*rest[:1])
    elif cmd == "status":
        status(*rest[:1])
    elif cmd == "github":
        github("--po" in rest)
    elif cmd == "guard":
        sys.exit(guard())
    else:
        print(USAGE)
