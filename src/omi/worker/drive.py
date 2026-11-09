"""`omi drive`: one detached loop per project that advances finished runs and starts ready tasks, stopping a task only on DECIDE."""

import contextlib
import datetime
import os
import re
import subprocess
import sys
import time

from ..common import core
from ..project import tasks, workflows
from ..state import resolve as state
from . import dispatch

POLL = 5  # seconds between passes


def session() -> str:
    """The driver's Coordinator session: its commands hold the task locks as one holder, alive while the driver runs."""
    return f"drive:{os.getpid()}"


def omi(project: state.Project, *args: str) -> tuple[int, str]:
    result = subprocess.run([sys.executable, "-m", "omi", *args], cwd=project.code, stdin=subprocess.DEVNULL, capture_output=True,
                            encoding="utf-8", errors="replace", env={**os.environ, "OMI_SESSION": session(), "OMI_BY": "drive"},
                            **({"creationflags": subprocess.CREATE_NO_WINDOW} if core.WINDOWS else {}))
    return result.returncode, (result.stdout + result.stderr).strip()


def announce(rec: dict, tid: str, action: str, waiting: dict[str, str], project: state.Project | None = None) -> None:
    """List the DECIDE in `waiting` and print it once per run (`decided` marker), whether or not `omi watch` reported the run;
    the driver lets go of the task's Coordinator lock: a DECIDE is the Coordinator's."""
    waiting[rec["dir"].name] = action
    if project is not None:
        dispatch.release(project, tid, session())
    marker = rec["dir"] / "decided"
    if not marker.exists() or marker.read_text(encoding="utf-8") != action:
        core.write_text(marker, action)
        print(f"{tid} {rec['role']}: {action}", flush=True)


def advance_finished(project: state.Project, waiting: dict[str, str]) -> bool:
    """`omi advance` the newest finished run of each open task whose next action is `NEXT:`; list `DECIDE:` ones in `waiting`."""
    found = tasks.tasks(project)
    worked = False
    for tid, rec in {r["tid"]: r for r in dispatch.records(project.code)}.items():
        meta = found.get(tid)
        if rec["running"] or not meta or meta.get("status") == "done":
            waiting.pop(rec["dir"].name, None)
            continue
        if (rec["dir"] / "driven").exists():
            if (rec["dir"] / "failed").exists():  # a restarted driver still waits for the Coordinator
                announce(rec, tid, (rec["dir"] / "failed").read_text(encoding="utf-8"), waiting, project)
            continue
        text = meta["_text"]
        action = dispatch.next_action(project, rec, text, dispatch.last_report(text, rec["role"], rec["started"]))
        if not action.startswith("NEXT:"):
            announce(rec, tid, action, waiting, project)
            continue
        waiting.pop(rec["dir"].name, None)
        core.write_text(rec["dir"] / "driven", "")  # one try per run; a failure waits for the Coordinator
        rc, out = omi(project, "advance", tid)
        worked = True
        print(f"advance {tid}: {'ok' if rc == 0 else f'FAILED rc={rc}'}\n{out}", flush=True)
        if rc == 0:
            core.write_text(rec["dir"] / "reported", "")
        else:
            action = f"DECIDE: advance failed (rc={rc}); fix the cause and rerun `omi advance {tid}`"
            core.write_text(rec["dir"] / "failed", action)
            announce(rec, tid, action, waiting, project)
    return worked


NOTE = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d) Coordinator \(", re.M)


def resume_idle(project: state.Project) -> bool:
    """Dispatch the current agent step of each idle in-progress task whose newest Coordinator note (`omi note`) is newer than its last run."""
    recs, worked = dispatch.records(project.code), False
    for tid, meta in tasks.tasks(project).items():
        mine = [r for r in recs if r["tid"] == tid]
        notes = NOTE.findall(meta.get("_text", "").partition("\n## Reports\n")[2])
        if meta.get("status") != "in-progress" or not notes or any(r["running"] for r in mine):
            continue
        noted = datetime.datetime.strptime(notes[-1], "%Y-%m-%d %H:%M")
        if mine and noted <= mine[-1]["started"].replace(second=0, microsecond=0):
            continue
        steps = workflows.get_workflow(project.state, meta.get("workflow") or workflows.DEFAULT_WORKFLOW)
        role = next((s["role"] for s in steps if s["id"] == meta.get("step")), workflows.COORDINATOR)
        if role == workflows.COORDINATOR or tasks.step_states(meta["_text"]).get(meta.get("step")) != "started":
            continue
        rc, out = omi(project, "dispatch", role, tid)
        worked = True
        print(f"resume {tid} {role} (Coordinator note {notes[-1]}){'' if rc == 0 else f' FAILED rc={rc}'}: {out}", flush=True)
    return worked


def stuck(recs: list[dict], waiting: dict[str, str]) -> bool:
    """True while the newest run of a task has a failed advance: no new work until the Coordinator acts (a newer run or done ends it)."""
    newest = {r["tid"]: r for r in recs}
    return any(r["dir"].name in waiting and (r["dir"] / "failed").exists() for r in newest.values())


def drive(project: state.Project, once: bool = False, poll: float = POLL, loop: float | None = None) -> None:
    """Loop until nothing runs and nothing is left to advance (`loop`: forever, polling every `loop` seconds when idle);
    one driver per project (drive.lock). The driver's commands share one Coordinator session, `drive:<pid>`."""
    runs = dispatch.runs_dir(project.code)
    runs.mkdir(parents=True, exist_ok=True)
    stack = contextlib.ExitStack()
    try:
        stack.enter_context(core.file_lock(runs / "drive.lock", 0))
    except TimeoutError:
        print("omi drive: already running")
        return
    with stack:
        waiting: dict[str, str] = {}
        recs = dispatch.records(project.code)
        finished = sum(not r["running"] for r in recs)
        while True:
            worked = advance_finished(project, waiting)
            worked = resume_idle(project) or worked  # idle in-progress tasks go before planned ones
            recs = dispatch.records(project.code)
            now = sum(not r["running"] for r in recs)
            free = dispatch.free_slots(project)
            if free and (now != finished or loop) and not stuck(recs, waiting):  # a run finished (looping: any pass) and a slot is free
                rc, out = omi(project, "dispatch", "next", "--max", str(free))
                print(f"dispatch next{'' if rc == 0 else f' FAILED rc={rc}'}: {out}", flush=True)
                worked = worked or not loop or "started " in out  # looping: a pass that started nothing is idle
            finished = now
            idle = not (worked or any(r["running"] for r in recs))
            if once or (idle and not loop):
                break
            time.sleep(loop if idle and loop else poll)
        for name, action in waiting.items():
            print(f"waiting for the Coordinator: {name}: {action}")
