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
from . import accept, dispatch


def diagnostic_tail(output: str) -> str:
    """Keep a short printable tail, removing terminal escapes and control characters."""
    output = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", output)
    output = "".join(c for c in output if c.isprintable() or c == "\n")
    return "\n".join(line[-500:] for line in output.strip().splitlines()[-10:])


def command(cwd: Path, argv: list[str], allowed: tuple[int, ...] = (0,)) -> str:
    """Run argv without a shell or console; never echo gh or push auth output."""
    result = subprocess.run(argv, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, encoding="utf-8", errors="replace",
                            **({"creationflags": subprocess.CREATE_NO_WINDOW} if core.WINDOWS else {}))
    if result.returncode not in allowed:
        git_readable = Path(argv[0]).stem.lower() == "git" and "push" not in argv[1:]
        omi_readable = argv[0] == sys.executable and argv[1:3] == ["-m", "omi"]
        tail = diagnostic_tail(result.stdout + "\n" + result.stderr) if git_readable or omi_readable else ""
        raise state.StateError(f"command exited {result.returncode}" + ("\n" + tail if tail else ""))
    return result.stdout.strip()


def commit_message(report: str, override: str | None) -> str:
    """Validate the untrusted report's one-line conventional commit subject."""
    found = re.findall(r"^Suggested commit:[ \t]*(.*)$", report, re.M)
    message = override if override is not None else (found[0] if len(found) == 1 else "")
    message = re.sub(r"^`([^`]*)`$", r"\1", message) if override is None else message
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
    reject: list[int] = field(default_factory=list)
    why: str | None = None
    round: int = 0
    findings: list[str] = field(default_factory=list)
    wt: Path = field(init=False)
    subject: str = field(init=False)
    meta: dict = field(init=False)
    report: str = field(init=False)
    step: dict = field(init=False)
    following: dict = field(init=False)
    fix: dict | None = None
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
    # A reproduce DONE whose report has `Reproduced:` also covers the same role's fix step that follows it.
    ctx.fix = None
    if (steps[at]["id"] == "reproduce" and at + 2 < len(steps) and steps[at + 1]["id"] == "fix"
            and steps[at + 1]["role"] == rec["role"] and re.search(r"^Reproduced:[ \t]*\S", report, re.M)):
        ctx.fix = steps[at + 1]
    last = at + 1 + (ctx.fix is not None)
    if last >= len(steps) or steps[last]["role"] not in tasks.REVIEW_ROLES:
        raise state.StateError("the next workflow step is not a reviewer")
    following = steps[last]
    if ctx.meta.get("step") != sid and not (ctx.fix and ctx.meta.get("step") == ctx.fix["id"]) and not (ctx.progress.get("step-done") and ctx.meta.get("step") == following["id"]):
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
    for s in (ctx.step, ctx.fix) if ctx.fix else (ctx.step,):
        if tasks.step_states(core.read_task(state.task_file(ctx.project, ctx.tid))).get(s["id"]) != "done":
            if core.meta(state.task_file(ctx.project, ctx.tid)).get("step") != s["id"]:
                omi(ctx, "step", ctx.tid, "next")
            omi(ctx, "step", ctx.tid, "done")


def step_next(ctx: Context) -> None:
    if core.meta(state.task_file(ctx.project, ctx.tid)).get("step") != ctx.following["id"]:
        omi(ctx, "step", ctx.tid, "next")


def reviewer(ctx: Context) -> None:
    # Recover a successful launch even if advance died before saving its marker.
    current = dispatch.records(ctx.project.code)
    if not any(r["tid"] == ctx.tid and r["role"] == ctx.following["role"] and r["started"] >= ctx.rec["started"] for r in current):
        omi(ctx, "dispatch", ctx.following["role"], ctx.tid)


class Stop(SystemExit):
    """A deliberate non-zero stop whose reason was already printed."""


FINDING = re.compile(r"- \S+:\d+")


def eligible_fail(ctx: Context) -> str:
    """Validate the newest review run as a FAIL for the current review step; returns the report."""
    rec = ctx.rec
    text = core.read_task(state.task_file(ctx.project, ctx.tid))
    report = dispatch.last_report(text, rec["role"], rec["started"])
    if rec["rc"] != 0 or dispatch.verdict(report) != "FAIL":
        raise state.StateError("newest finished run is not a write role with DONE or a review role with FAIL")
    wt = core.task_worktrees(ctx.project.code).get(ctx.tid)
    if not wt:
        raise state.StateError("task worktree is missing")
    ctx.wt = Path(wt)
    ctx.meta = core.parse(text)
    steps = workflows.get_workflow(ctx.project.state, ctx.meta.get("workflow") or workflows.DEFAULT_WORKFLOW)
    sid = ctx.progress.get("step", ctx.meta.get("step"))
    ctx.step = next((s for s in steps if s["id"] == sid), {})
    if not ctx.step or ctx.step["role"] != rec["role"]:
        raise state.StateError("run role does not match the current review step")
    log = text.partition("\n## Steps\n")[2].split("\n## ", 1)[0]
    starts = re.findall(rf"^- {re.escape(sid)} started (\d{{4}}-\d\d-\d\d \d\d:\d\d)", log, re.M)
    if not starts or datetime.datetime.strptime(starts[-1], "%Y-%m-%d %H:%M") > rec["started"].replace(second=0, microsecond=0):
        raise state.StateError("finished run is stale for the current step")
    if not ctx.progress.get("step-back") and (ctx.meta.get("step") != sid or tasks.step_states(text).get(sid) != "started"):
        raise state.StateError("finished run is not for the current step")
    if any(r["running"] and not (ctx.progress.get("step-back") and r["role"] != rec["role"])
           for r in dispatch.records(ctx.project.code) if r["tid"] == ctx.tid):
        raise state.StateError("task has a running worker")
    ctx.findings = [l for l in report.splitlines() if FINDING.match(l)]
    if not ctx.findings:
        raise state.StateError("the FAIL report has no finding lines (- <file:line> ...)")
    ctx.progress["step"] = sid
    ctx.round = ctx.progress.setdefault("round", tasks.failed_rounds(text))
    return report


def record_findings(ctx: Context) -> str:
    task = state.task_file(ctx.project, ctx.tid)
    text = core.read_task(task)
    head, sep, rest = text.partition("\n## Checkpoint\n")
    body, sep2, tail = rest.partition("\n## ")
    marker = f"Review round {ctx.round} FAIL:"
    if not sep or not sep2:
        raise state.StateError("task file has no ## Checkpoint section before another section")
    if re.search(rf"^{re.escape(marker)}", body, re.M):
        return "already recorded"
    kept = [f for n, f in enumerate(ctx.findings, 1) if n not in ctx.reject]
    why = " ".join((ctx.why or "").split())
    lines = [marker, *kept, *(f"Coordinator rejected finding {n}: {why}" for n in ctx.reject)]
    core.write_text(task, head + sep + body.rstrip("\n") + "\n" + tasks.clean_text("\n".join(lines)) + "\n" + sep2 + tail)
    return f"{len(kept)} finding(s) under {marker}"


def step_back(ctx: Context) -> str:
    try:
        out = omi(ctx, "step", ctx.tid, "back", *(["--why", ctx.why] if ctx.why else []))
    except state.StateError as exc:
        limit = next((l for l in str(exc).splitlines() if l.startswith("ROUND LIMIT")), None)
        if limit:
            print(limit)
            raise Stop(1) from exc
        raise
    ctx.progress["replan"] = next((l for l in out.splitlines() if l.startswith("REPLAN")), "")
    return "done"


def pr_back_to_draft(ctx: Context) -> str:
    select_remote(ctx)
    if not ctx.target:
        return "skipped (no GitHub remote)"
    open_prs = json.loads(gh(ctx, "list", "--state", "open", "--head", f"task/{ctx.tid}", "--json", "number,isDraft"))
    ready = [p for p in open_prs if not p.get("isDraft")]
    if not ready:
        return "skipped (no open non-draft PR)"
    gh(ctx, "ready", "--undo", str(ready[0]["number"]))
    return "back to draft"


def engineer(ctx: Context) -> str:
    text = core.read_task(state.task_file(ctx.project, ctx.tid))
    meta = core.parse(text)
    steps = workflows.get_workflow(ctx.project.state, meta.get("workflow") or workflows.DEFAULT_WORKFLOW)
    role = next(s["role"] for s in steps if s["id"] == meta.get("step"))
    if ctx.progress.get("replan") and role != "omi-agent-architect":
        print(ctx.progress["replan"])
        raise Stop(1)
    if not any(r["tid"] == ctx.tid and r["role"] == role and r["started"] >= ctx.rec["started"] for r in dispatch.records(ctx.project.code)):
        omi(ctx, "dispatch", role, ctx.tid)
    return f"{role} dispatched"


def advance_fail(ctx: Context) -> None:
    ctx.report = eligible_fail(ctx)
    print(f"eligibility: review FAIL for {ctx.step['id']}, round {ctx.round}")
    if ctx.reject and (bad := [n for n in ctx.reject if not 1 <= n <= len(ctx.findings)]):
        raise state.StateError(f"--reject {bad}: the report has {len(ctx.findings)} finding(s)")
    if ctx.reject and not (ctx.why or "").strip():
        raise state.StateError('--reject needs --why "<reason>"')
    if not [n for n in range(1, len(ctx.findings) + 1) if n not in ctx.reject]:
        print("all findings rejected: nothing stepped back; the Coordinator decides (override with `omi step done --po` or fix)")
        raise Stop(1)
    perform(ctx, "findings", record_findings)
    perform(ctx, "step-back", step_back)
    perform(ctx, "pr-draft", pr_back_to_draft)
    perform(ctx, "dispatch", engineer)


def auto_dispatch(ctx: Context) -> str:
    """After a merge, start the next ready tasks (free slots under `auto_dispatch_max`); a failure never undoes the merge."""
    free = dispatch.free_slots(ctx.project)
    if not free:
        return "skipped (auto_dispatch_max is 0 or no free slot)"
    try:
        return omi(ctx, "dispatch", "next", "--max", str(free))
    except state.StateError as exc:
        return f"FAILED (the merge is done): {exc}"


def advance(project: state.Project, tid: str, message: str | None = None, reject: list[int] | None = None, why: str | None = None) -> None:
    """Advance only the newest successful run: a DONE write run to its reviewer, a review FAIL back to the engineer, or a review PASS through acceptance; stop at the first failed stage."""
    ctx = None
    try:
        rec = newest_run(project, tid)
        with core.file_lock(rec["dir"] / "advance.lock", 0):
            path = rec["dir"] / "advance.json"
            progress = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
            ctx = Context(project, tid, rec, progress, message, reject or [], why)
            if rec["role"] in tasks.REVIEW_ROLES or catalogs.get_role(project.state, rec["role"])["access"] == "read":
                report = dispatch.last_report(core.read_task(state.task_file(project, tid)), rec["role"], rec["started"])
                if dispatch.verdict(report) == "PASS":
                    try:
                        accept.advance_pass(ctx, perform, command)
                    finally:
                        if ctx.progress.get("ci-failed"):
                            save_progress(ctx)
                    if ctx.progress.get("post-merge-test"):
                        perform(ctx, "auto-dispatch", auto_dispatch)
                    return
                return advance_fail(ctx)
            if reject or why:
                raise state.StateError("--reject and --why apply only after a review FAIL")
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
    except Stop:
        raise
    except (SystemExit, state.StateError, OSError, ValueError, TimeoutError) as exc:
        stage = ctx.stage if ctx else "eligibility"
        raise SystemExit(f"advance {stage} FAILED: {exc}") from exc
