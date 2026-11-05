"""Tests for omi dispatch / watch: run records, two runs finishing together, lost wrappers, parallel refusal."""
import contextlib
import datetime
import io
import os
import signal
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import helpers
import omi.setup.upgrade
from omi.state import resolve as state
from omi.worker import dispatch

SRC = {"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}
GATE = "import os,sys,time\nwhile not os.path.exists(sys.argv[1]): time.sleep(0.05)\nsys.exit(int(sys.argv[2]))"


def make_task(root, tid, scope, report=None):
    future = f"{datetime.datetime.now() + datetime.timedelta(hours=1):%Y-%m-%d %H:%M}"
    body = f"## Reports\n{future} omi-agent-engineer (claude):\n> {report}\n" if report else ""
    (root / ".omi/tasks" / f"{tid}.md").write_text(
        f"---\nid: {tid}\nstatus: in-progress\nscope: {scope}\nrole: omi-agent-engineer\n---\n## Checkpoint\nDone:\n\n{body}", encoding="utf-8")


def watch(project, *flags):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        dispatch.watch(project, "--wait" in flags, "--all" in flags)
    return out.getvalue()


def test_two_runs_finish_together() -> None:
    with patch.dict(os.environ, SRC), tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        omi.setup.upgrade.init(root)
        make_task(root, "TASK-001", "a/**", "DONE\nSuggested commit: x")
        make_task(root, "TASK-002", "b/**", "NEEDS SCOPE: c.py")
        make_task(root, "TASK-003", "a/x.py")
        helpers.git(root, "add", ".")
        helpers.git(root, "commit", "-qm", "base")
        project = state.resolve(root)
        gate = root / "gate"
        with contextlib.redirect_stdout(io.StringIO()):
            dispatch.launch(project, "TASK-001", "omi-agent-engineer", [sys.executable, "-c", GATE, str(gate), "0"])
            dispatch.launch(project, "TASK-002", "omi-agent-engineer", [sys.executable, "-c", GATE, str(gate), "0"])
        try:  # scope overlap with a running task, and the same task twice
            dispatch.launch(project, "TASK-003", "omi-agent-engineer", [sys.executable, "-c", "pass"])
            raise AssertionError("overlap not refused")
        except state.StateError as exc:
            assert "overlap" in str(exc)
        try:
            dispatch.launch(project, "TASK-001", "omi-agent-engineer", [sys.executable, "-c", "pass"])
            raise AssertionError("duplicate not refused")
        except state.StateError as exc:
            assert "already has a running worker" in str(exc)
        out = watch(project)
        assert out.count("running:") == 2 and "finished:" not in out, out
        gate.write_text("", encoding="utf-8")
        while any(r["running"] for r in dispatch.records(root)):
            time.sleep(0.05)
        out = watch(project)
        assert out.count("finished:") == 2, out
        assert "TASK-001 omi-agent-engineer rc=0 verdict=DONE" in out and "NEXT: diff and scope check" in out, out
        assert "TASK-002 omi-agent-engineer rc=0 verdict=NEEDS SCOPE" in out and "DECIDE: NEEDS SCOPE" in out, out
        assert "no new finished runs" in watch(project)
        assert watch(project, "--all").count("finished:") == 2


def test_lost_wrapper_and_exit_codes() -> None:
    with patch.dict(os.environ, SRC), tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        omi.setup.upgrade.init(root)
        make_task(root, "TASK-001", "a/**")
        make_task(root, "TASK-002", "b/**")
        helpers.git(root, "add", ".")
        helpers.git(root, "commit", "-qm", "base")
        project = state.resolve(root)
        with contextlib.redirect_stdout(io.StringIO()):
            hook = dispatch.launch(project, "TASK-001", "omi-agent-engineer", [sys.executable, "-c", "import sys; sys.exit(6)"])
            while not (hook / "rc").exists():
                time.sleep(0.05)
            if not dispatch.core.WINDOWS:
                lost = dispatch.launch(project, "TASK-002", "omi-agent-engineer", [sys.executable, "-c", "import time; time.sleep(3)"])
                os.kill(int((lost / "started").read_text(encoding="utf-8")), signal.SIGKILL)
                while dispatch.alive(lost):  # the kernel releases the lock asynchronously
                    time.sleep(0.05)
        out = watch(project)
        assert "rc=6" in out and "DECIDE: hook failed" in out, out
        if not dispatch.core.WINDOWS:
            assert "rc=LOST" in out and "DECIDE: LOST" in out, out


def main():
    test_two_runs_finish_together()
    test_lost_wrapper_and_exit_codes()


if __name__ == "__main__":
    main()
