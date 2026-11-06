"""Host-side, restartable handoff from a finished write run to its reviewer."""

import datetime
import json
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from ..common import core
from ..project import catalogs, scope, tasks, workflows
from ..state import resolve as state
from . import dispatch


def diagnostic_tail(output: str) -> str:
    """Keep a short printable tail, removing terminal escapes and control characters."""
    output = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", output)
    output = "".join(c for c in output if c.isprintable() or c == "\n")
    return "\n".join(line[-500:] for line in output.strip().splitlines()[-10:])


def command(cwd: Path, argv: list[str]) -> str:
    """Run argv without a shell or console; never echo gh or push auth output."""
    result = subprocess.run(argv, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, encoding="utf-8", errors="replace",
                            **({"creationflags": subprocess.CREATE_NO_WINDOW} if core.WINDOWS else {}))
    if result.returncode:
        git_readable = Path(argv[0]).stem.lower() == "git" and "push" not in argv[1:]
        omi_readable = argv[0] == sys.executable and argv[1:3] == ["-m", "omi"]
        tail = diagnostic_tail(result.stdout + "\n" + result.stderr) if git_readable or omi_readable else ""
        raise state.StateError(f"command exited {result.returncode}" + ("\n" + tail if tail else ""))
    return result.stdout.strip()


def commit_message(report: str, override: str | None) -> str:
    """Validate the untrusted report's one-line conventional commit subject."""
    found = re.findall(r"^Suggested commit:[ \t]*(.*)$", report, re.M)
    message = override if override is not None else (found[0] if len(found) == 1 else "")
    if (not message or any(ord(c) < 32 or 127 <= ord(c) <= 159 or c in "\u2028\u2029" for c in message)
            or not re.fullmatch(r"(?:feat|fix|docs|chore|refactor|test|ci|build|perf|style|revert)(?:\([^()\s]+\))?!?: [^\s].*", message)):
        raise state.StateError('missing or invalid Suggested commit; supply --message "<msg>" (one conventional commit line)')
    return message


@dataclass
class Context:
    """Validated handoff inputs and the shared progress owned by this advance call."""
    project: state.Project
    tid: str
    rec: dict
    progress: dict
    message: str | None = None
    wt: Path = field(init=False)
    subject: str = field(init=False)
    meta: dict = field(init=False)
    report: str = field(init=False)
    step: dict = field(init=False)
    following: dict = field(init=False)
    stage: str = "eligibility"
    target: str = ""
    repository: str = ""


def git(ctx: Context, *args: str) -> str:
    return command(ctx.wt, ["git", *args])


def omi(ctx: Context, *args: str) -> str:
    return command(ctx.project.code, [sys.executable, "-m", "omi", *args])


def gh(ctx: Context, *args: str) -> str:
    return command(ctx.wt, ["gh", "pr", *args, "--repo", ctx.repository])


def newest_run(project: state.Project, tid: str) -> dict:
    if not re.fullmatch(r"TASK-\d+", tid):
        raise state.StateError("expected TASK-<number>")
    finished = [r for r in dispatch.records(project.code) if r["tid"] == tid and not r["running"]]
    if not finished:
        raise state.StateError("no finished run")
    return finished[-1]


def eligible(ctx: Context) -> tuple[dict, str, dict, dict]:
    """Validate the write run against the current step before any stage mutates git."""
    rec = ctx.rec
    text = core.read_task(state.task_file(ctx.project, ctx.tid))
    report = dispatch.last_report(text, rec["role"], rec["started"])
    if rec["rc"] != 0 or dispatch.verdict(report) != "DONE":
        raise state.StateError("newest finished run must exit 0 with verdict DONE")
    if catalogs.get_role(ctx.project.state, rec["role"])["access"] != "write":
        raise state.StateError("newest finished run is not a write role")
    ctx.subject = commit_message(report, ctx.message)
    wt = core.task_worktrees(ctx.project.code).get(ctx.tid)
    if not wt:
        raise state.StateError("task worktree is missing")
    ctx.wt = Path(wt)
    if git(ctx, "branch", "--show-current") != f"task/{ctx.tid}":
        raise state.StateError("worktree is not on the task branch")
    ctx.meta = core.parse(text)
    steps = workflows.get_workflow(ctx.project.state, ctx.meta.get("workflow") or workflows.DEFAULT_WORKFLOW)
    sid = ctx.progress.get("step", ctx.meta.get("step"))
    at = next((i for i, s in enumerate(steps) if s["id"] == sid), -1)
    if at < 0 or steps[at]["role"] != rec["role"]:
        raise state.StateError("run role does not match the current write step")
    starts = re.findall(rf"^- {re.escape(sid)} started (\d{{4}}-\d\d-\d\d \d\d:\d\d)",
                        text.partition("\n## Steps\n")[2].split("\n## ", 1)[0], re.M)
    if not starts or datetime.datetime.strptime(starts[-1], "%Y-%m-%d %H:%M") > rec["started"].replace(second=0, microsecond=0):
        raise state.StateError("finished run is stale for the current step")
    if at + 1 >= len(steps) or steps[at + 1]["role"] not in tasks.REVIEW_ROLES:
        raise state.StateError("the next workflow step is not a reviewer")
    following = steps[at + 1]
    if ctx.meta.get("step") != sid and not (ctx.progress.get("step-done") and ctx.meta.get("step") == following["id"]):
        raise state.StateError("finished run is not for the current step")
    recs = [r for r in dispatch.records(ctx.project.code) if r["tid"] == ctx.tid]
    if any(r["running"] and not (ctx.progress.get("step-next") and r["role"] == following["role"]) for r in recs):
        raise state.StateError("task has a running worker")
    if ctx.progress.get("head") and git(ctx, "rev-parse", "HEAD") != ctx.progress["head"]:
        raise state.StateError("HEAD changed since advance; finish a fresh write run")
    ctx.progress["step"] = sid
    return rec, report, steps[at], following


def save_progress(ctx: Context) -> None:
    path = ctx.rec["dir"] / "advance.json"
    core.write_text(path.with_suffix(".tmp"), json.dumps(ctx.progress))
    path.with_suffix(".tmp").replace(path)


def perform(ctx: Context, name: str, action: Callable[[Context], str | None], remember: bool = True) -> None:
    ctx.stage = name
    if remember and ctx.progress.get(name):
        print(name + ": skipped (already done)")
        return
    detail = action(ctx)
    if remember:
        ctx.progress[name] = True
        save_progress(ctx)
    print(name + ": " + (detail or "done"))


def check_scope(ctx: Context) -> str:
    # These checked reads make scope's permissive git-read failures fail closed.
    git(ctx, "status", "--porcelain", "-z", "-uall", "--no-renames")
    git(ctx, "diff", "--name-only", "-z", "--no-renames", "development...HEAD")
    bad = scope.out_of_scope(ctx.wt, ctx.tid, committed=True)
    if bad:
        for path in bad:
            print("OUT OF SCOPE: " + path)
        raise state.StateError("changed paths exceed the authoritative scope; nothing committed or reverted")
    return "checked"


def commit(ctx: Context) -> str:
    dirty = git(ctx, "status", "--porcelain", "-uall")
    if dirty:
        git(ctx, "add", "-A", "--", ".")
        git(ctx, "commit", "-m", ctx.subject)
    ctx.progress["head"] = git(ctx, "rev-parse", "HEAD")
    return "committed" if dirty else "nothing to commit"


def ensure_clean(ctx: Context) -> None:
    dirty = git(ctx, "status", "--porcelain", "--", ".", f":(exclude).omi/tasks/{ctx.tid}.md")
    if dirty:
        raise state.StateError("worktree changed since commit; finish a fresh write run")


def rebase(ctx: Context) -> None:
    try:
        git(ctx, "rebase", "development")
    except state.StateError as exc:
        git(ctx, "rebase", "--abort")
        raise state.StateError(f"rebase failed; aborted: {exc}") from exc
    ctx.progress["head"] = git(ctx, "rev-parse", "HEAD")


def select_remote(ctx: Context) -> None:
    ctx.stage = "remote"
    remotes = git(ctx, "remote").splitlines()
    for name in sorted(remotes, key=lambda name: name != "origin"):
        remote = state.normalise_url(git(ctx, "remote", "get-url", name))
        if remote.startswith("github.com/"):
            ctx.target, ctx.repository = name, remote.removeprefix("github.com/")
            break


def push(ctx: Context) -> None:
    # Eligibility pins this to task/<TID>; never force-update development.
    git(ctx, "push", "--force-with-lease", "-u", ctx.target, f"task/{ctx.tid}")


def draft(ctx: Context) -> None:
    existing = json.loads(gh(ctx, "list", "--state", "open", "--head", f"task/{ctx.tid}", "--json", "number"))
    if not existing:
        body = ctx.rec["dir"] / "pr-body.md"
        core.write_text(body, tasks.clean_text(
            f"## Summary\n{ctx.tid}: {ctx.meta.get('title', ctx.subject)}\n\n## Changes\n{ctx.report}\n\n"
            "## Not in this PR\nNone.\n\n## Verification\nHost test and reviews pending.\n\n## Known issues\nNone reported.\n"))
        gh(ctx, "create", "--draft", "--base", "development", "--head", f"task/{ctx.tid}",
           "--title", f"[{ctx.tid}] {ctx.subject}", "--body-file", str(body))


def host_test(ctx: Context) -> None:
    omi(ctx, "host-test", ctx.tid)


def step_done(ctx: Context) -> None:
    if tasks.step_states(core.read_task(state.task_file(ctx.project, ctx.tid))).get(ctx.step["id"]) != "done":
        omi(ctx, "step", ctx.tid, "done")


def step_next(ctx: Context) -> None:
    if core.meta(state.task_file(ctx.project, ctx.tid)).get("step") != ctx.following["id"]:
        omi(ctx, "step", ctx.tid, "next")


def reviewer(ctx: Context) -> None:
    # Recover a successful launch even if advance died before saving its marker.
    current = dispatch.records(ctx.project.code)
    if not any(r["tid"] == ctx.tid and r["role"] == ctx.following["role"] and r["started"] >= ctx.rec["started"] for r in current):
        omi(ctx, "dispatch", ctx.following["role"], ctx.tid)


def advance(project: state.Project, tid: str, message: str | None = None) -> None:
    """Advance only the newest successful write run; stop at the first failed stage."""
    ctx = None
    try:
        rec = newest_run(project, tid)
        with core.file_lock(rec["dir"] / "advance.lock", 0):
            path = rec["dir"] / "advance.json"
            progress = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
            ctx = Context(project, tid, rec, progress, message)
            ctx.rec, ctx.report, ctx.step, ctx.following = eligible(ctx)
            print("eligibility: DONE write run for " + ctx.step["id"])
            perform(ctx, "scope", check_scope, remember=False)
            perform(ctx, "commit", commit)
            ensure_clean(ctx)
            perform(ctx, "rebase", rebase)
            select_remote(ctx)
            if ctx.target:
                perform(ctx, "push", push)
                perform(ctx, "pr", draft)
            else:
                print("push: skipped (no GitHub remote)")
                print("pr: skipped (no GitHub remote)")
            perform(ctx, "host-test", host_test)
            perform(ctx, "step-done", step_done)
            perform(ctx, "step-next", step_next)
            perform(ctx, "dispatch", reviewer)
    except (SystemExit, state.StateError, OSError, ValueError, TimeoutError) as exc:
        stage = ctx.stage if ctx else "eligibility"
        raise SystemExit(f"advance {stage} FAILED: {exc}") from exc
