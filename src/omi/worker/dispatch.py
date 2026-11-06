"""Detached `omi run` launcher, per-run records and `omi watch`: every finished run is reported once with its next action."""

import datetime
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from ..common import core
from ..project import catalogs, tasks
from ..state import resolve as state
from . import docker, tools

START_GRACE = 10  # seconds launch() waits for the wrapper
STAMP = "%Y%m%d-%H%M%S"
WRITE_DONE = "NEXT: python -m omi advance {tid}"
READ_PASS = "NEXT: python -m omi advance {tid}"
READ_FAIL = "NEXT: python -m omi advance {tid}"


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


def launch(project: state.Project, tid: str, role: str, argv: list[str] | None = None) -> Path:
    """Start the run detached; refuse when it conflicts with a running task."""
    running = [r for r in records(project.code) if r["running"]]
    if any(r["tid"] == tid for r in running):
        raise state.StateError(f"{tid} already has a running worker. Nothing started.")
    others = list(dict.fromkeys(r["tid"] for r in running))
    if others:
        bad = [c for c in tasks.parallel(project, [tid, *others]) if "overlap" in c or "depends on" in c]
        if bad:
            raise state.StateError("not parallel-safe with running tasks:\n" + "\n".join(bad) + "\nNothing started.")
    rundir = runs_dir(project.code) / f"{tid}-{role}-{datetime.datetime.now():{STAMP}}"
    rundir.mkdir(parents=True)
    argv = argv or [sys.executable, "-m", "omi", "run", role, tid]
    core.write_text(rundir / "argv.json", json.dumps({"tid": tid, "role": role, "argv": argv}))
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
            rc = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT).returncode
        core.write_text(rundir / "rc.tmp", str(rc))
        os.replace(rundir / "rc.tmp", rundir / "rc")


def last_report(text: str, role: str, since: datetime.datetime) -> str:
    """Body of the newest `## Reports` entry of `role` written since `since` (minute precision), or ''."""
    body = text.partition("\n## Reports\n")[2].split("\n## ", 1)[0]
    found = ""
    for m in re.finditer(rf"^(\d{{4}}-\d\d-\d\d \d\d:\d\d) {re.escape(role)} \(.*?\):\n((?:>.*\n?)*)", body, re.M):
        if datetime.datetime.strptime(m[1], "%Y-%m-%d %H:%M") >= since.replace(second=0):
            found = "\n".join(l.removeprefix(">").strip() for l in m[2].splitlines())
    return found


def verdict(report: str) -> str:
    m = re.match(r"\W*(DONE|BLOCKED|NEEDS SCOPE)\b", report)
    return m[1] if m else tools.verdict_of(report) or "n/a"


def killed(rc: int | None) -> bool:
    """Recognize signal exits and Windows control-event / NTSTATUS termination codes."""
    return rc is not None and (rc < 0 or (core.WINDOWS and (rc == 0x40010004 or rc >= 0x80000000)))


def next_action(project: state.Project, rec: dict, text: str, report: str) -> str:
    """One line: `NEXT:` the deterministic follow-up, or `DECIDE:` what the Coordinator must judge."""
    tid, rc, v = rec["tid"], rec["rc"], verdict(report)
    if rc is None:
        return f"DECIDE: LOST, the wrapper died without an exit code; check docker and {rec['dir'] / 'log'}, then rerun"
    if killed(rc):
        return f"DECIDE: LOST, killed: rerun; check docker and {rec['dir'] / 'log'}"
    if v == "NEEDS SCOPE":
        return f"DECIDE: {report.splitlines()[0]}; widen scope or file a new task; see the report and the log"
    why = {3: "out of scope or plan violation: accept the paths (NEEDS SCOPE) or revert them",
           5: "usage limit on every tool: wait, or rerun with another tool/model (TASK-216)",
           6: "hook failed: the task cannot move on until it is fixed"}.get(rc)
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
