"""Host-side, restartable handoff from a finished write run to its reviewer."""

import datetime
import json
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from ..common import core
from ..project import catalogs, scope, tasks, workflows
from ..state import resolve as state
from . import dispatch


def command(cwd: Path, argv: list[str]) -> str:
    """Run argv without a shell or console; never echo remote/auth output."""
    result = subprocess.run(argv, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, encoding="utf-8", errors="replace",
                            **({"creationflags": subprocess.CREATE_NO_WINDOW} if core.WINDOWS else {}))
    if result.returncode:
        raise state.StateError(f"command exited {result.returncode}")
    return result.stdout.strip()


def commit_message(report: str, override: str | None) -> str:
    """Validate the untrusted report's one-line conventional commit subject."""
    found = re.findall(r"^Suggested commit:[ \t]*(.*)$", report, re.M)
    message = override if override is not None else (found[0] if len(found) == 1 else "")
    if (not message or any(ord(c) < 32 or 127 <= ord(c) <= 159 or c in "\u2028\u2029" for c in message)
            or not re.fullmatch(r"(?:feat|fix|docs|chore|refactor|test|ci|build|perf|style|revert)(?:\([^()\s]+\))?!?: [^\s].*", message)):
        raise state.StateError('missing or invalid Suggested commit; supply --message "<msg>" (one conventional commit line)')
    return message


def advance(project: state.Project, tid: str, message: str | None = None) -> None:
    """Advance only the newest successful write run; stop at the first failed stage."""
    stage = "eligibility"
    try:
        if not re.fullmatch(r"TASK-\d+", tid):
            raise state.StateError("expected TASK-<number>")
        recs = [r for r in dispatch.records(project.code) if r["tid"] == tid]
        finished = [r for r in recs if not r["running"]]
        if not finished:
            raise state.StateError("no finished run")
        rec = finished[-1]
        text = core.read_task(state.task_file(project, tid))
        report = dispatch.last_report(text, rec["role"], rec["started"])
        if rec["rc"] != 0 or dispatch.verdict(report) != "DONE":
            raise state.StateError("newest finished run must exit 0 with verdict DONE")
        if catalogs.get_role(project.state, rec["role"])["access"] != "write":
            raise state.StateError("newest finished run is not a write role")
        subject = commit_message(report, message)
        wt_value = core.task_worktrees(project.code).get(tid)
        if not wt_value:
            raise state.StateError("task worktree is missing")
        wt = Path(wt_value)
        git = lambda *args: command(wt, ["git", *args])  # noqa: E731
        if git("branch", "--show-current") != f"task/{tid}":
            raise state.StateError("worktree is not on the task branch")
        progress_file = rec["dir"] / "advance.json"
        with core.file_lock(rec["dir"] / "advance.lock", 0):
            progress = json.loads(progress_file.read_text(encoding="utf-8")) if progress_file.exists() else {}
            meta = core.parse(text)
            steps = workflows.get_workflow(project.state, meta.get("workflow") or workflows.DEFAULT_WORKFLOW)
            sid = progress.get("step", meta.get("step"))
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
            if meta.get("step") != sid and not (progress.get("step-done") and meta.get("step") == following["id"]):
                raise state.StateError("finished run is not for the current step")
            if any(r["running"] and not (progress.get("step-next") and r["role"] == following["role"]) for r in recs):
                raise state.StateError("task has a running worker")
            if progress.get("head") and git("rev-parse", "HEAD") != progress["head"]:
                raise state.StateError("HEAD changed since advance; finish a fresh write run")
            progress["step"] = sid
            print("eligibility: DONE write run for " + sid)

            def save() -> None:
                core.write_text(progress_file.with_suffix(".tmp"), json.dumps(progress))
                progress_file.with_suffix(".tmp").replace(progress_file)

            def perform(name: str, action: Callable[[], str | None]) -> None:
                nonlocal stage
                stage = name
                if progress.get(name):
                    print(name + ": skipped (already done)")
                    return
                detail = action()
                progress[name] = True
                save()
                print(name + ": " + (detail or "done"))

            stage = "scope"
            # These checked reads make scope's permissive git-read failures fail closed.
            git("status", "--porcelain", "-z", "-uall", "--no-renames")
            git("diff", "--name-only", "-z", "--no-renames", "development...HEAD")
            bad = scope.out_of_scope(wt, tid, committed=True)
            if bad:
                for path in bad:
                    print("OUT OF SCOPE: " + path)
                raise state.StateError("changed paths exceed the authoritative scope; nothing committed or reverted")
            print("scope: checked")

            def commit() -> str:
                if git("status", "--porcelain", "-uall"):
                    git("add", "-A", "--", ".")
                    git("commit", "-m", subject)
                progress["head"] = git("rev-parse", "HEAD")
                return "done (clean worktree)"

            perform("commit", commit)
            if progress.get("commit"):
                stage = "commit"
                dirty = git("status", "--porcelain", "--", ".", f":(exclude).omi/tasks/{tid}.md")
                if dirty:
                    raise state.StateError("worktree changed since commit; finish a fresh write run")

            def rebase() -> None:
                try:
                    git("rebase", "development")
                except state.StateError:
                    git("rebase", "--abort")
                    raise state.StateError("rebase failed; aborted")
                progress["head"] = git("rev-parse", "HEAD")

            perform("rebase", rebase)
            stage = "remote"
            remotes = git("remote").splitlines()
            target, repository = "", ""
            for name in sorted(remotes, key=lambda name: name != "origin"):
                remote = state.normalise_url(git("remote", "get-url", name))
                if remote.startswith("github.com/"):
                    target, repository = name, remote.removeprefix("github.com/")
                    break
            if target:
                perform("push", lambda: (git("push", "-u", target, f"task/{tid}") and None))

                def draft() -> None:
                    gh = lambda *args: command(wt, ["gh", "pr", *args, "--repo", repository])  # noqa: E731
                    existing = json.loads(gh("list", "--state", "open", "--head", f"task/{tid}", "--json", "number"))
                    if not existing:
                        body = rec["dir"] / "pr-body.md"
                        core.write_text(body, tasks.clean_text(f"## Summary\n{tid}: {meta.get('title', subject)}\n\n## Changes\n{report}\n\n## Not in this PR\nNone.\n\n## Verification\nHost test and reviews pending.\n\n## Known issues\nNone reported.\n"))
                        gh("create", "--draft", "--base", "development", "--head", f"task/{tid}",
                           "--title", f"[{tid}] {subject}", "--body-file", str(body))

                perform("pr", draft)
            else:
                print("push: skipped (no GitHub remote)")
                print("pr: skipped (no GitHub remote)")

            omi = lambda *args: command(project.code, [sys.executable, "-m", "omi", *args])  # noqa: E731
            perform("host-test", lambda: (omi("host-test", tid) and None))

            def done() -> None:
                if tasks.step_states(core.read_task(state.task_file(project, tid))).get(sid) != "done":
                    omi("step", tid, "done")

            def next_step() -> None:
                if core.meta(state.task_file(project, tid)).get("step") != following["id"]:
                    omi("step", tid, "next")

            perform("step-done", done)
            perform("step-next", next_step)

            def reviewer() -> None:
                # Recover a successful launch even if advance died before saving its marker.
                current = dispatch.records(project.code)
                if not any(r["tid"] == tid and r["role"] == following["role"] and r["started"] >= rec["started"] for r in current):
                    omi("dispatch", following["role"], tid)

            perform("dispatch", reviewer)
    except (SystemExit, state.StateError, OSError, ValueError, TimeoutError) as exc:
        raise SystemExit(f"advance {stage} FAILED: {exc}") from exc
