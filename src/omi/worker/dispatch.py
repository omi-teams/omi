"""Detached `omi run` launcher, per-run records and `omi watch`: every finished run is reported once with its next action."""

import contextlib
import datetime
import io
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from ..common import core
from ..project import catalogs, structure, tasks, tree, workflows
from ..state import resolve as state
from ..state import sync as state_sync
from . import docker, tools

START_GRACE = 10  # seconds launch() waits for the wrapper
STAMP = "%Y%m%d-%H%M%S"
WRITE_DONE = "NEXT: python -m omi advance {tid}"
READ_PASS = "NEXT: python -m omi advance {tid}"
READ_FAIL = "NEXT: python -m omi advance {tid}"
STOPPED_RC = 10  # rc written by `omi stop`; the `stopped` marker names who


def runs_dir(code: Path) -> Path:
    common = core.git(code, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if not common:
        raise state.StateError(f"cannot find the shared git directory for {code}")
    return Path(common) / "omi-runs"


def alive(rundir: Path) -> bool:
    """True while the wrapper holds run.lock (the OS releases it when the wrapper dies), or while a fresh record awaits its wrapper."""
    if not (rundir / "started").exists():  # no lock file yet: probing would create it; wait as long as launch() does
        return time.time() - (rundir / "argv.json").stat().st_mtime < START_GRACE
    try:
        with core.file_lock(rundir / "run.lock", 0):
            return False
    except TimeoutError:
        return True


def records(code: Path) -> list[dict]:
    """Every run record, oldest first: rc is None while running or lost."""
    found = []
    for d in sorted(runs_dir(code).glob("TASK-*-*")):
        try:
            info = json.loads((d / "argv.json").read_text(encoding="utf-8"))
            rc = int((d / "rc").read_text(encoding="utf-8")) if (d / "rc").exists() else None
        except (OSError, ValueError):
            continue  # being written
        live = rc is None and alive(d)
        if rc is None and not live and (d / "rc").exists():  # rc landed between the two checks
            rc = int((d / "rc").read_text(encoding="utf-8"))
        found.append({"dir": d, "tid": info["tid"], "role": info["role"], "rc": rc, "running": live,
                      "reported": (d / "reported").exists(),
                      "started": datetime.datetime.strptime(d.name.rsplit("-", 2)[1] + "-" + d.name.rsplit("-", 2)[2], STAMP)})
    return sorted(found, key=lambda r: r["started"])


def holders(project: state.Project, found: dict[str, dict], idle: bool = True) -> list[str]:
    """Tasks holding their scope: those with a running worker, plus (idle) every other in-progress task."""
    containers = tree.children_map(found)
    return list(dict.fromkeys([*(r["tid"] for r in records(project.code) if r["running"]),
                               *(t for t, m in found.items() if idle and m.get("status") == "in-progress" and t not in containers)]))


def held_by(project: state.Project, tid: str, others: list[str]) -> list[str]:
    """Scope overlaps and dependencies between `tid` and the tasks in `others`, each naming the holder."""
    return [f"{other} holds the scope: {c}" for other in others if other != tid
            for c in tasks.parallel(project, [tid, other]) if "overlap" in c or "depends on" in c]


def size_flags(project: state.Project, tid: str, role: str, meta: dict) -> list[str]:
    """`--model`/`--effort` from the role's `small:` (model/effort) for a task naming at most 3 non-test files, when the task
    leaves model, effort and step_settings empty; a routed choice goes under the task's `## Runs` (the role default is not written)."""
    if not meta or any(meta.get(k) for k in ("model", "effort", "step_settings")):
        return []
    am, size = catalogs.get_role(project.state, role), workflows.task_size(meta)
    small = am.get("small") if size is not None and size <= workflows.SMALL_FILES else None
    if not small:
        return []
    tasks.append_note(state.task_file(project, tid), "Runs", f"- dispatch {role}: {size} non-test file(s) -> small {small}")
    model, _, effort = (small or "").partition("/")
    return [*(["--model", model] if model else []), *(["--effort", effort] if effort else [])]


LOCK_IDLE = 1800  # seconds a lock without a known holder pid stays held after its last use


def session() -> tuple[str, int | None]:
    """(Coordinator session id, pid whose life holds the lock): OMI_SESSION (`drive:<pid>`), else the Claude Code session
    (pid CLAUDE_PID; None when unset: the lock then lives LOCK_IDLE seconds after its last use), else the parent."""
    sid = os.environ.get("OMI_SESSION") or os.environ.get("CLAUDE_CODE_SESSION_ID") or f"pid:{os.getppid()}"
    claude = sid == os.environ.get("CLAUDE_CODE_SESSION_ID") and not os.environ.get("OMI_SESSION")
    pid = os.environ.get("CLAUDE_PID", "") if claude else sid.rsplit(":", 1)[-1]
    return sid, int(pid) if pid.isdigit() else (None if claude else os.getppid())


def holder_alive(held: dict, path: Path) -> bool:
    """The lock holder still counts: its pid runs, or (no pid recorded) the lock was used in the last LOCK_IDLE seconds."""
    if held.get("pid") is None:
        return bool(held.get("session")) and time.time() - path.stat().st_mtime < LOCK_IDLE
    return core.pid_alive(held.get("pid"))


def claim(project: state.Project, tid: str, release: bool = False) -> None:
    """Take the per-task Coordinator lock (`<runs>/<ID>.coordinator`) for this session; a live other holder refuses in one line,
    a holder whose process is gone is taken over. `release`: drop it after the check (a dispatch hands the task to its run)."""
    try:
        runs = runs_dir(project.code)
    except state.StateError:
        return  # not a git checkout: no runs to coordinate
    runs.mkdir(parents=True, exist_ok=True)
    path, (sid, pid) = runs / f"{tid}.coordinator", session()
    with core.file_lock(runs / "coordinator.lock", 10):
        try:
            held = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            held = {}
        if held.get("session") not in (None, sid) and holder_alive(held, path):
            raise state.StateError(f"{tid} is driven by Coordinator session {held['session']} (pid {held['pid']}); nothing changed")
        if release:
            path.unlink(missing_ok=True)
        else:  # rewritten on every use: a holder without a pid stays held LOCK_IDLE seconds after its last command
            core.write_text(path, json.dumps({"session": sid, "pid": pid}))


def release(project: state.Project, tid: str, sid: str | None = None) -> None:
    """Drop the task's Coordinator lock when this session holds it (the driver stops at a DECIDE)."""
    with contextlib.suppress(OSError, ValueError, state.StateError):
        path = runs_dir(project.code) / f"{tid}.coordinator"
        if json.loads(path.read_text(encoding="utf-8")).get("session") == (sid or session()[0]):
            path.unlink()


def new_record(project: state.Project, tid: str, role: str, argv: list[str], by: str) -> Path:
    """A run directory with argv.json naming who dispatched it (advance, drive, dispatch next, Coordinator)."""
    runs_dir(project.code).mkdir(parents=True, exist_ok=True)
    while True:  # one record per second per task and role: a second run in the same second waits for the next one
        rundir = runs_dir(project.code) / f"{tid}-{role}-{datetime.datetime.now():{STAMP}}"
        try:
            rundir.mkdir()
            break
        except FileExistsError:
            time.sleep(0.2)
    core.write_text(rundir / "argv.json", json.dumps({"tid": tid, "role": role, "argv": argv, "by": by}))
    return rundir


def foreground(project: state.Project, tid: str, role: str, argv: list[str], fn) -> int:
    """Foreground `omi run`: the same record as a detached run (argv.json, started, run.lock, rc) around fn(); inside a wrapper, just fn()."""
    try:
        runs_dir(project.code)
    except state.StateError:
        return fn()
    if os.environ.get("OMI_RUN_DIR"):
        return fn()
    rundir = new_record(project, tid, role, argv, os.environ.get("OMI_BY") or "Coordinator")
    rc = 1
    with core.file_lock(rundir / "run.lock", 10):
        core.write_text(rundir / "started", str(os.getpid()))
        os.environ["OMI_RUN_DIR"] = str(rundir)
        try:
            rc = fn()
        except SystemExit as exc:
            rc = exc.code if isinstance(exc.code, int) else 1
            raise
        finally:
            os.environ.pop("OMI_RUN_DIR", None)
            core.write_text(rundir / "rc", str(rc))
    return rc


def stop(project: state.Project, tid: str, who: str = "Coordinator") -> list[str]:
    """`omi stop <ID>`: mark each running run `stopped`, kill its wrapper tree and every container of the task, write rc."""
    stopped = []
    for r in records(project.code):
        if r["tid"] != tid or not r["running"]:
            continue
        core.write_text(r["dir"] / "stopped", who)  # first: a dying run must not resume through the hook-fix path
        pid = (r["dir"] / "started").read_text(encoding="utf-8").strip() if (r["dir"] / "started").exists() else ""
        docker.kill(pids=[int(pid)] if pid.isdigit() and int(pid) != os.getpid() else [])
        stopped.append(r)
    if stopped:
        docker.kill(containers=docker.task_containers(project.state if project.detached else project.code, tid))
    for r in stopped:
        with contextlib.suppress(TimeoutError):  # the killed wrapper released run.lock
            with core.file_lock(r["dir"] / "run.lock", 10):
                if not (r["dir"] / "rc").exists():
                    core.write_text(r["dir"] / "rc", str(STOPPED_RC))
        print(f"stopped {tid} {r['role']} ({r['dir'].name}) by {who}")
    if not stopped:
        print(f"{tid}: no running run")
    return [r["dir"].name for r in stopped]


def launch(project: state.Project, tid: str, role: str, argv: list[str] | None = None, by: str | None = None) -> Path:
    """Start the run detached; refuse when it conflicts with a running task, and a not yet started task also with idle in-progress ones.
    Reviewers of one task may run together (a workflow `stage:`)."""
    running = {r["role"] for r in records(project.code) if r["running"] and r["tid"] == tid}
    if running and not (role in tasks.REVIEW_ROLES and running <= set(tasks.REVIEW_ROLES) - {role}):
        raise state.StateError(f"{tid} already has a running worker. Nothing started.")
    found = tasks.tasks(project)
    bad = held_by(project, tid, holders(project, found, idle=found.get(tid, {}).get("status", "planned") == "planned"))
    if bad:
        raise state.StateError("not parallel-safe with in-progress tasks:\n" + "\n".join(bad) + "\nNothing started.")
    claim(project, tid, release=True)  # the run now drives the task; a live other Coordinator refuses
    argv = argv or [sys.executable, "-m", "omi", "run", role, tid]
    if "--model" not in argv and "--effort" not in argv:
        argv = [*argv, *size_flags(project, tid, role, found.get(tid, {}))]
    rundir = new_record(project, tid, role, argv, by or os.environ.get("OMI_BY") or "Coordinator")
    command = [sys.executable, "-W", "ignore::RuntimeWarning", "-m", "omi.worker.dispatch"]
    with (rundir / "log").open("a", encoding="utf-8", newline="\n") as log:
        if core.WINDOWS:
            # Reap the short-lived parent before returning, so tree kills cannot find the wrapper.
            result = subprocess.run([*command, "--spawn", str(rundir)], cwd=project.code, stdin=subprocess.DEVNULL,
                                    stdout=subprocess.PIPE, stderr=log, text=True, encoding="utf-8", check=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            print(result.stdout, end="")  # forward any breakaway warning from the spawner
        else:
            subprocess.Popen([*command, str(rundir)], cwd=project.code, stdin=subprocess.DEVNULL,
                             stdout=log, stderr=log, start_new_session=True)
    deadline = time.monotonic() + 10
    while not (rundir / "started").exists():
        if time.monotonic() > deadline:
            raise state.StateError(f"the run wrapper did not start; see {rundir}")
        time.sleep(0.05)
    print(f"started {role} on {tid}: {rundir.name} (omi watch)")
    return rundir


def config(project: state.Project, key: str, default: object) -> object:
    """`key` from .omi/config.json, else `default`."""
    try:
        return json.loads((project.state / ".omi" / "config.json").read_text(encoding="utf-8")).get(key, default)
    except (OSError, ValueError, AttributeError):
        return default


def free_slots(project: state.Project) -> int:
    """`auto_dispatch_max` (default 1, 0 = off) minus the tasks running now."""
    limit = config(project, "auto_dispatch_max", 1)
    limit = limit if isinstance(limit, int) and not isinstance(limit, bool) and limit >= 0 else 1
    return max(0, limit - len({r["tid"] for r in records(project.code) if r["running"]}))


def driver_running(project: state.Project) -> bool:
    """True while `omi drive` holds drive.lock (the OS releases it when the driver dies)."""
    runs = runs_dir(project.code)
    runs.mkdir(parents=True, exist_ok=True)
    try:
        with core.file_lock(runs / "drive.lock", 0):
            return False
    except TimeoutError:
        return True


def start_driver(project: state.Project) -> None:
    """Start `omi drive` detached unless it runs already or `auto_drive` is false in config."""
    if config(project, "auto_drive", True) is False or driver_running(project):
        return
    flags = {"start_new_session": True}
    if core.WINDOWS:
        flags = {"creationflags": subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_BREAKAWAY_FROM_JOB}
    log_path = runs_dir(project.code) / "drive.log"
    with log_path.open("a", encoding="utf-8", newline="\n") as log:
        for attempt in range(2):
            try:
                subprocess.Popen([sys.executable, "-W", "ignore::RuntimeWarning", "-m", "omi", "drive"], cwd=project.code,
                                 stdin=subprocess.DEVNULL, stdout=log, stderr=log, **flags)
                break
            except OSError as exc:
                if not core.WINDOWS or attempt or getattr(exc, "winerror", None) != 5:
                    raise
                flags["creationflags"] &= ~subprocess.CREATE_BREAKAWAY_FROM_JOB  # the host job forbids breakaway
    print(f"omi drive started: advances finished runs and starts ready tasks (log: {log_path})")


def dispatch_next(project: state.Project, maximum: int = 1) -> None:
    """Start ready planned tasks in status order, stopping at the first launch failure."""
    if maximum < 1:
        raise state.StateError("--max must be a positive integer")
    found = tasks.rolled_up(tasks.tasks(project))
    containers = tree.children_map(found)
    held = holders(project, found)
    picked = []
    for tid, meta in found.items():
        if meta.get("status", "planned") != "planned":
            continue
        if tid in containers:
            print(f"skip {tid}: has child tasks")
            continue
        reason = ""
        deps = [d for d in core.split(meta.get("depends")) if found.get(d, {}).get("status") != "done"]
        if deps:
            reason = "depends not done: " + ", ".join(deps)
        elif not core.split(meta.get("scope")):
            reason = "no scope"
        else:
            try:
                skills = catalogs.task_skill_ids(project.state, meta)
                catalogs.check_skills(project.state, skills)
                reason = "" if skills else "no skills picked"
            except SystemExit as exc:
                reason = " ".join(str(exc).splitlines())
        if not reason:
            conflicts = held_by(project, tid, list(dict.fromkeys([*held, *picked])))
            if conflicts:
                reason = "; ".join(conflicts)
        if not reason and len(picked) >= maximum:
            reason = f"max {maximum} reached"
        if reason:
            print(f"skip {tid}: {reason}")
            continue
        task = state.task_file(project, tid)
        steps = workflows.get_workflow(project.state, meta.get("workflow") or workflows.DEFAULT_WORKFLOW)
        first = next((s for s in steps if s["role"] != workflows.COORDINATOR), None)
        if first is None:
            raise state.StateError(f"{tid}: workflow has no agent step")
        if catalogs.get_role(project.state, first["role"])["access"] == "write":
            structure.require_map(project.state)  # before the task changes: no write step without the approved map
        with contextlib.redirect_stdout(io.StringIO()):
            core.write_text(task, tasks.set_front(core.read_task(task), "status", "in-progress"))
            owner = project if project.detached else state.Project(state=task.parents[2], code=project.code)
            root = state_sync.repo(owner)
            state_sync.commit(owner, [task.relative_to(root).as_posix()], f"{tid}: start task")
            wt = core.task_worktrees(project.code).get(tid)
            if not wt:
                wt = project.code.parent / f"{project.code.name}.wt" / tid
                if core.git(project.code, "worktree", "add", str(wt), "-b", f"task/{tid}", "development") is None:
                    raise state.StateError(f"{tid}: git worktree add failed for {wt}")
            step_root = project if project.detached else Path(wt)
            task = state.task_file(project, tid)
            while True:
                current = core.meta(task)
                sid = current.get("step")
                if not sid or tasks.step_states(current["_text"]).get(sid) in ("done", "skipped"):
                    tasks.step(step_root, tid, "next")
                    current = core.meta(task)
                    sid = current.get("step")
                if sid == first["id"]:
                    break
                selected = next((s for s in steps if s["id"] == sid), None)
                if selected is None or selected["role"] != workflows.COORDINATOR:
                    raise state.StateError(f"{tid}: expected first agent step {first['id']}, got {sid}")
                tasks.step(step_root, tid, "skip", why="dispatch next: task file has scope, skills and criteria")
            if project.detached:
                state_sync.commit(project, [task.relative_to(root).as_posix()], f"{tid}: first agent step")
        argv = [sys.executable, "-m", "omi", "run", first["role"], tid]
        for key in ("tool", "model", "effort"):
            if meta.get(key):
                argv.extend([f"--{key}", meta[key]])
        launch(project, tid, first["role"], argv, by="dispatch next")
        picked.append(tid)
    if not picked:
        print("dispatch next: nothing ready")


def spawn(rundir: Path) -> None:
    """Windows intermediary: start the wrapper and exit, orphaning it before launch() returns."""
    flags = {"creationflags": subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_BREAKAWAY_FROM_JOB}
    with (rundir / "log").open("a", encoding="utf-8", newline="\n") as log:  # wrapper start-up errors land in the log too
        for attempt in range(2):
            try:
                subprocess.Popen([sys.executable, "-W", "ignore::RuntimeWarning", "-m", "omi.worker.dispatch", str(rundir)], cwd=Path.cwd(), stdin=subprocess.DEVNULL,
                                 stdout=log, stderr=log, **flags)
                break
            except OSError as exc:
                if not core.WINDOWS or attempt or getattr(exc, "winerror", None) != 5:
                    raise
                # Jobs without JOB_OBJECT_LIMIT_BREAKAWAY_OK reject breakaway with access denied.
                flags["creationflags"] &= ~subprocess.CREATE_BREAKAWAY_FROM_JOB
                print("warning: the host job forbids breakaway; retrying without it. This run dies with the session.")


def wrap(rundir: Path) -> None:
    """Wrapper process: hold run.lock, run the command, write rc last (inside the lock, atomically)."""
    argv = json.loads((rundir / "argv.json").read_text(encoding="utf-8"))["argv"]
    with core.file_lock(rundir / "run.lock", 10):
        core.write_text(rundir / "started", str(os.getpid()))
        with (rundir / "log").open("a", encoding="utf-8", newline="\n") as log:
            rc = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                env={**os.environ, "OMI_RUN_DIR": str(rundir)}).returncode  # quiet test logs land here
        core.write_text(rundir / "rc.tmp", str(rc))
        os.replace(rundir / "rc.tmp", rundir / "rc")


def reports(text: str, role: str) -> list[tuple[datetime.datetime, str]]:
    """Every `## Reports` entry of `role`, oldest first, as (minute, body without the `>` quoting)."""
    body = text.partition("\n## Reports\n")[2].split("\n## ", 1)[0]
    return [(datetime.datetime.strptime(m[1], "%Y-%m-%d %H:%M"), "\n".join(l.removeprefix(">").strip() for l in m[2].splitlines()))
            for m in re.finditer(rf"^(\d{{4}}-\d\d-\d\d \d\d:\d\d) {re.escape(role)} \(.*?\):\n((?:>.*\n?)*)", body, re.M)]


def last_report(text: str, role: str, since: datetime.datetime) -> str:
    """Body of the newest `## Reports` entry of `role` written since `since` (minute precision), or ''."""
    return next((r for at, r in reversed(reports(text, role)) if at >= since.replace(second=0)), "")


def verdict(report: str) -> str:
    """The verdict opening the report, or alone on a line (`**DONE**`); never a word inside a sentence."""
    m = re.match(r"\W*(DONE|BLOCKED|NEEDS SCOPE)\b", report) or re.search(r"^[ \t*_`]*(DONE|BLOCKED|NEEDS SCOPE)[ \t*_`]*$", report, re.M)
    return m[1] if m else tools.verdict_of(report) or "n/a"


def killed(rc: int | None) -> bool:
    """Recognize signal exits and Windows control-event / NTSTATUS termination codes."""
    return rc is not None and (rc < 0 or (core.WINDOWS and (rc == 0x40010004 or rc >= 0x80000000)))


def next_action(project: state.Project, rec: dict, text: str, report: str) -> str:
    """One line: `NEXT:` the deterministic follow-up, or `DECIDE:` what the Coordinator must judge."""
    tid, rc, v = rec["tid"], rec["rc"], verdict(report)
    if rc is None:
        return f"DECIDE: LOST, the wrapper died without an exit code; check docker and {rec['dir'] / 'log'}, then rerun"
    if (rec["dir"] / "stopped").exists():
        return f"DECIDE: STOPPED by {(rec['dir'] / 'stopped').read_text(encoding='utf-8').strip() or 'Coordinator'}; rerun when ready"
    if rc == 9:
        return "DECIDE: TIMEOUT, the run passed its run_timeout and was killed (see Checkpoint); rescope, raise run_timeout or rerun"
    if rc == 8:
        auth = rec["dir"] / "auth"
        return "DECIDE: " + (auth.read_text(encoding="utf-8").strip() if auth.exists() else "AUTH: login invalid; log in on the host")
    if killed(rc):
        return f"DECIDE: LOST, killed: rerun; check docker and {rec['dir'] / 'log'}"
    if v == "NEEDS SCOPE":
        return f"DECIDE: {report.splitlines()[0]}; widen scope or file a new task; see the report and the log"
    why = {3: "out of scope or plan violation: accept the paths (NEEDS SCOPE) or revert them",
           5: "usage limit on every tool: wait, or rerun with another tool/model (TASK-216)",
           6: "hook failed: the task cannot move on until it is fixed",
           7: "BUDGET: the run passed its token_budget (see Checkpoint): split or rescope the task, or raise token_budget in .omi/config.json"}.get(rc)
    if why or v == "BLOCKED" or rc:
        return f"DECIDE: {why or (v if v != 'n/a' else f'exit {rc}')}; see the report and the log"
    access = catalogs.load_roles(project.state).get(rec["role"], {}).get("access")
    if access == "write":
        return WRITE_DONE.format(tid=tid) if v == "DONE" else "DECIDE: no DONE in the report; read it and the log"
    if v == "PASS":
        return READ_PASS.format(tid=tid)
    if v == "FAIL":
        try:
            tasks.round_gate(project.state, tid, text, None)
        except SystemExit:
            return 'DECIDE: review round limit reached; the Coordinator decides: rescope, replan, or one more round with --why "<reason>"'
        return READ_FAIL.format(tid=tid)
    return "DECIDE: reviewer gave no PASS or FAIL; read the report"


def watch(project: state.Project, wait: bool = False, show_all: bool = False) -> None:
    """Print running workers, then each finished run not yet reported (all: the whole history) and mark it reported."""
    while True:
        recs = records(project.code)
        fresh = [r for r in recs if not r["running"] and (show_all or not r["reported"])]
        if fresh or not wait or not any(r["running"] for r in recs):
            break
        time.sleep(2)
    found = tasks.tasks(project)
    for r in recs:
        if r["running"]:
            print(f"running: {r['tid']} {r['role']} since {r['started']:%H:%M:%S} ({r['dir'].name})")
    docker.print_workers(project)
    for r in fresh:
        text = found.get(r["tid"], {}).get("_text", "")
        report = last_report(text, r["role"], r["started"])
        print(f"finished: {r['tid']} {r['role']} rc={'LOST' if r['rc'] is None or killed(r['rc']) else r['rc']} verdict={verdict(report)} ({r['dir'].name})")
        print("  " + next_action(project, r, text, report))
        if r["rc"] is not None:
            tail = (r["dir"] / "log").read_text(encoding="utf-8", errors="replace").strip().splitlines()[-1:]
            print("  log: " + (tail[0] if tail else "(empty)"))
        core.write_text(r["dir"] / "reported", "")
    if not fresh and not any(r["running"] for r in recs):
        print("no running workers, no new finished runs")


if __name__ == "__main__":
    if sys.argv[1] == "--spawn":
        spawn(Path(sys.argv[2]))
    else:
        wrap(Path(sys.argv[1]))
