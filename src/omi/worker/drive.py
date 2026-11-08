"""`omi drive`: one detached loop per project that advances finished runs and starts ready tasks, stopping a task only on DECIDE."""

import contextlib
import subprocess
import sys
import time

from ..common import core
from ..project import tasks
from ..state import resolve as state
from . import dispatch

POLL = 5  # seconds between passes


def omi(project: state.Project, *args: str) -> tuple[int, str]:
    result = subprocess.run([sys.executable, "-m", "omi", *args], cwd=project.code, stdin=subprocess.DEVNULL, capture_output=True,
                            encoding="utf-8", errors="replace",
                            **({"creationflags": subprocess.CREATE_NO_WINDOW} if core.WINDOWS else {}))
    return result.returncode, (result.stdout + result.stderr).strip()


def announce(rec: dict, tid: str, action: str, waiting: dict[str, str]) -> None:
    """List the DECIDE in `waiting` and print it once per run (`decided` marker), whether or not `omi watch` reported the run."""
    waiting[rec["dir"].name] = action
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
                announce(rec, tid, (rec["dir"] / "failed").read_text(encoding="utf-8"), waiting)
            continue
        text = meta["_text"]
        action = dispatch.next_action(project, rec, text, dispatch.last_report(text, rec["role"], rec["started"]))
        if not action.startswith("NEXT:"):
            announce(rec, tid, action, waiting)
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
            announce(rec, tid, action, waiting)
    return worked


def stuck(recs: list[dict], waiting: dict[str, str]) -> bool:
    """True while the newest run of a task has a failed advance: no new work until the Coordinator acts (a newer run or done ends it)."""
    newest = {r["tid"]: r for r in recs}
    return any(r["dir"].name in waiting and (r["dir"] / "failed").exists() for r in newest.values())


def drive(project: state.Project, once: bool = False, poll: float = POLL) -> None:
    """Loop until nothing runs and nothing is left to advance; one driver per project (drive.lock)."""
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
            recs = dispatch.records(project.code)
            now = sum(not r["running"] for r in recs)
            free = dispatch.free_slots(project)
            if free and now != finished and not stuck(recs, waiting):  # a run finished and a slot is free
                rc, out = omi(project, "dispatch", "next", "--max", str(free))
                print(f"dispatch next{'' if rc == 0 else f' FAILED rc={rc}'}: {out}", flush=True)
                worked = True
            finished = now
            if once or not (worked or any(r["running"] for r in recs)):
                break
            time.sleep(poll)
        for name, action in waiting.items():
            print(f"waiting for the Coordinator: {name}: {action}")
