"""Tests for omi dispatch / watch: run records, two runs finishing together, lost wrappers, parallel refusal."""
import contextlib
import datetime
import io
import os
import runpy
import warnings
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


@contextlib.contextmanager
def windows_launch():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        project = state.Project(state=root, code=root)
        def started(argv, **kwargs):
            (Path(argv[-1]) / "started").write_text("123", encoding="utf-8")
        def spawner(argv, **kwargs):
            out = io.StringIO()
            with patch.object(sys, "argv", argv[4:]), contextlib.chdir(kwargs["cwd"]), contextlib.redirect_stdout(out), warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                runpy.run_module("omi.worker.dispatch", run_name="__main__")
            return dispatch.subprocess.CompletedProcess(argv, 0, stdout=out.getvalue())
        with patch.object(dispatch.core, "WINDOWS", True), \
                patch.object(dispatch.subprocess, "DETACHED_PROCESS", 8, create=True), \
                patch.object(dispatch.subprocess, "CREATE_NO_WINDOW", 0x08000000, create=True), \
                patch.object(dispatch.subprocess, "CREATE_NEW_PROCESS_GROUP", 512, create=True), \
                patch.object(dispatch.subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0x01000000, create=True), \
                patch.object(dispatch, "records", return_value=[]), \
                patch.object(dispatch, "runs_dir", return_value=root / "runs"), \
                patch.object(dispatch.subprocess, "Popen", side_effect=started) as popen, \
                patch.object(dispatch.subprocess, "run", side_effect=spawner) as run:
            yield project, popen, started, run


def test_windows_launch_uses_spawner() -> None:
    with windows_launch() as (project, popen, _, run), contextlib.redirect_stdout(io.StringIO()):
        rundir = dispatch.launch(project, "TASK-227", "omi-agent-engineer")
        assert run.call_count == 1, "Windows launch must wait for a short-lived spawner"
        assert run.call_args.args[0][-2:] == ["--spawn", str(rundir)]
        assert run.call_args.kwargs["creationflags"] == 0x08000000
        assert run.call_args.kwargs["check"] is True
        assert run.call_args.kwargs["cwd"] == project.code
        assert popen.call_args.args[0][-1] == str(rundir)
        assert "--spawn" not in popen.call_args.args[0]
        assert popen.call_args.kwargs["cwd"] == project.code
        assert (rundir / "started").exists()


def test_windows_launch_waits_for_wrapper() -> None:
    with windows_launch() as (project, popen, started, run), contextlib.redirect_stdout(io.StringIO()):
        popen.side_effect = lambda *a, **kw: None
        with patch.object(dispatch.time, "sleep", side_effect=lambda _: started(popen.call_args.args[0])) as sleep:
            dispatch.launch(project, "TASK-227", "omi-agent-engineer")
        assert run.call_count == 1
        sleep.assert_called_once_with(0.05)


def test_posix_launch_stays_direct() -> None:
    with windows_launch() as (project, popen, _, run), patch.object(dispatch.core, "WINDOWS", False), \
            contextlib.redirect_stdout(io.StringIO()):
        rundir = dispatch.launch(project, "TASK-227", "omi-agent-engineer")
        run.assert_not_called()
        assert popen.call_count == 1
        assert popen.call_args.args[0][-1] == str(rundir)
        assert "--spawn" not in popen.call_args.args[0]
        assert popen.call_args.kwargs["start_new_session"] is True
        assert "creationflags" not in popen.call_args.kwargs


def test_windows_spawner_failure_propagates() -> None:
    with windows_launch() as (project, popen, _, run), contextlib.redirect_stdout(io.StringIO()):
        error = dispatch.subprocess.CalledProcessError(1, ["spawner"])
        run.side_effect = error
        try:
            dispatch.launch(project, "TASK-227", "omi-agent-engineer")
        except dispatch.subprocess.CalledProcessError as exc:
            assert exc is error
        else:
            raise AssertionError("spawner failure was swallowed")
        popen.assert_not_called()


def test_windows_launch_breaks_away() -> None:
    with windows_launch() as (project, popen, _, _), contextlib.redirect_stdout(io.StringIO()) as out:
        dispatch.launch(project, "TASK-227", "omi-agent-engineer")
        assert popen.call_count == 1
        assert popen.call_args.kwargs["creationflags"] == 0x08000000 | 512 | 0x01000000
        assert "warning" not in out.getvalue().lower()


def test_windows_launch_breakaway_denied() -> None:
    denied = OSError("job forbids breakaway")
    denied.winerror = 5
    with windows_launch() as (project, popen, started, _), contextlib.redirect_stdout(io.StringIO()) as out:
        def launch(argv, **kwargs):
            if popen.call_count == 1:
                raise denied
            return started(argv, **kwargs)
        popen.side_effect = launch
        dispatch.launch(project, "TASK-227", "omi-agent-engineer")
        assert popen.call_count == 2
        assert [c.kwargs["creationflags"] for c in popen.call_args_list] == [0x08000000 | 512 | 0x01000000, 0x08000000 | 512]
        assert popen.call_args_list[0].args == popen.call_args_list[1].args
        assert "warning" in out.getvalue().lower() and "dies with the session" in out.getvalue()


def test_windows_launch_errors_propagate() -> None:
    for winerror, expected_calls in ((2, 1), (5, 2)):
        error = OSError("launch failed")
        error.winerror = winerror
        with windows_launch() as (project, popen, _, _), contextlib.redirect_stdout(io.StringIO()):
            popen.side_effect = error
            try:
                dispatch.launch(project, "TASK-227", "omi-agent-engineer")
            except OSError as exc:
                assert exc is error
            else:
                raise AssertionError("launch failure was swallowed")
            assert popen.call_count == expected_calls


def test_watch_windows_termination_codes() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        project = state.Project(state=root, code=root)
        (root / "log").write_text("interrupted\n", encoding="utf-8")
        rec = {"tid": "TASK-227", "role": "omi-agent-engineer", "dir": root,
               "started": datetime.datetime(2026, 11, 6), "running": False, "reported": False}
        text = "\n## Reports\n2026-11-06 00:00 omi-agent-engineer (codex):\n> DONE\n"
        for rc in (1073807364, 0x80000000, 0xFFFFFFFF, -1073741510, -1, 0, 6, 0x40010003, 0x7FFFFFFF):
            killed = rc == 1073807364 or rc >= 0x80000000 or rc < 0
            with patch.object(dispatch.core, "WINDOWS", True), \
                    patch.object(dispatch, "records", return_value=[{**rec, "rc": rc}]), \
                    patch.object(dispatch.tasks, "tasks", return_value={"TASK-227": {"_text": text}}), \
                    patch.object(dispatch.docker, "print_workers"), \
                    patch.object(dispatch.catalogs, "load_roles", return_value={"omi-agent-engineer": {"access": "write"}}):
                out = watch(project)
            if killed:
                assert "rc=LOST" in out and "killed: rerun" in out, out
                assert "NEXT:" not in out and f"exit {rc}" not in out, out
            else:
                assert f"rc={rc}" in out and "killed: rerun" not in out, out


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
        assert "TASK-001 omi-agent-engineer rc=0 verdict=DONE" in out and "NEXT: python -m omi advance TASK-001" in out, out
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


def test_needs_scope_over_hook_failure() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        project = state.Project(state=root, code=root)
        started = datetime.datetime(2026, 11, 5, 22, 11)
        rec = {"tid": "TASK-225", "role": "omi-agent-engineer", "rc": 6, "dir": root,
               "started": started, "running": False, "reported": False}
        (root / "log").write_text("post-run hook failed: the task cannot move to review\n", encoding="utf-8")
        for report in ("NEEDS SCOPE: src/extra.py, tests/test_extra.py - cover the affected behavior", "NEEDS SCOPE"):
            text = (f"\n## Reports\n2026-11-05 22:11 omi-agent-engineer (codex):\n> {report}\n"
                    "2026-11-05 22:11 hook post-run FAILED (exit 1):\n> missing coverage\n")
            with patch.object(dispatch, "records", return_value=[rec]), \
                    patch.object(dispatch.tasks, "tasks", return_value={"TASK-225": {"_text": text}}), \
                    patch.object(dispatch.docker, "print_workers"):
                out = watch(project)
            assert "rc=6 verdict=NEEDS SCOPE" in out, out
            assert "DECIDE: NEEDS SCOPE" in out and "DECIDE: hook failed" not in out, out
            assert "widen scope" in out and "new task" in out, out
            if ":" in report:
                assert "src/extra.py, tests/test_extra.py" in out, out


def test_record_before_wrapper_starts() -> None:
    with patch.dict(os.environ, SRC), tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        omi.setup.upgrade.init(root)
        make_task(root, "TASK-001", "a/**")
        helpers.git(root, "add", ".")
        helpers.git(root, "commit", "-qm", "base")
        project = state.resolve(root)
        rundir = dispatch.runs_dir(root) / "TASK-001-omi-agent-engineer-20261105-100000"
        rundir.mkdir(parents=True)
        (rundir / "argv.json").write_text('{"tid": "TASK-001", "role": "omi-agent-engineer", "argv": []}', encoding="utf-8")
        assert [(r["running"], r["rc"]) for r in dispatch.records(root)] == [(True, None)]
        assert "running:" in watch(project) and "finished:" not in watch(project) and not (rundir / "run.lock").exists()
        old = time.time() - 60
        os.utime(rundir / "argv.json", (old, old))
        assert "rc=LOST" in watch(project)


def test_watch_round_limit() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        project = state.Project(state=root, code=root)
        rec = {"tid": "TASK-228", "role": "omi-agent-reviewer", "rc": 0, "dir": root,
               "started": datetime.datetime(2026, 11, 6), "running": False, "reported": False}
        row = "| omi-agent-reviewer | m | high | 1 | 1 | 1 | 1s | - | FAIL |\n"
        text = ("\n## Usage\n| role | model |\n|---|---|\n" + row * 2
                + "\n## Reports\n2026-11-06 00:00 omi-agent-reviewer (codex):\n> VERDICT: FAIL\n")
        (root / "log").write_text("review finished\n", encoding="utf-8")
        with patch.object(dispatch, "records", return_value=[rec]), \
                patch.object(dispatch.tasks, "tasks", return_value={"TASK-228": {"_text": text}}), \
                patch.object(dispatch.docker, "print_workers"), \
                patch.object(dispatch.catalogs, "load_roles", return_value={"omi-agent-reviewer": {"access": "read"}}):
            out = watch(project)
        assert ('DECIDE: review round limit reached; the Coordinator decides: rescope, replan, '
                'or one more round with --why "<reason>"') in out, out
        assert "PO" not in out, out


def test_reviewer_next_action() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        omi.setup.upgrade.init(root)
        project = state.resolve(root)
        rec = {"tid": "TASK-001", "role": "omi-agent-reviewer", "rc": 0, "dir": root}
        row = "| omi-agent-reviewer | m | high | 1 | 1 | 1 | 1s | - | FAIL |\n"
        one, two = "\n## Usage\n| role | model |\n|---|---|\n" + row, "\n## Usage\n| role | model |\n|---|---|\n" + row * 2
        assert dispatch.next_action(project, rec, "", "VERDICT: PASS") == dispatch.READ_PASS.format(tid=rec["tid"])
        assert dispatch.next_action(project, rec, one, "VERDICT: FAIL") == dispatch.READ_FAIL.format(tid="TASK-001") == "NEXT: python -m omi advance TASK-001"
        assert "round limit" in dispatch.next_action(project, rec, two, "VERDICT: FAIL")
        assert dispatch.next_action(project, rec, "", "no verdict").startswith("DECIDE")


def test_records_sort_across_roles() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        for role, stamp in [('omi-agent-engineer', '20261106-120000'), ('omi-agent-reviewer', '20261106-110000')]:
            directory = root / f'TASK-218-{role}-{stamp}'
            directory.mkdir()
            (directory / 'argv.json').write_text('{"tid": "TASK-218", "role": "' + role + '"}', encoding='utf-8')
            (directory / 'rc').write_text('0', encoding='utf-8')
        with patch.object(dispatch, 'runs_dir', return_value=root):
            assert [r['role'] for r in dispatch.records(root)] == ['omi-agent-reviewer', 'omi-agent-engineer']


@contextlib.contextmanager
def next_fixture():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve() / "code"
        root.mkdir()
        omi.setup.upgrade.init(root)
        helpers.git(root, "add", ".")
        helpers.git(root, "commit", "-qm", "base")
        helpers.git(root, "branch", "-m", "development")
        project = state.resolve(root)
        def planned(tid, scope="a.py", extra=""):
            path = root / ".omi/tasks" / f"{tid}.md"
            path.write_text(f"---\nid: {tid}\nstatus: planned\nscope: {scope}\n"
                            f"tool: codex\nmodel: task-model\neffort: high\n{extra}---\n"
                            "## Acceptance criteria\n- [ ] works\n\n## Checkpoint\nDone:\n", encoding="utf-8")
            return path
        with patch.object(dispatch, "records", return_value=[]), \
                patch.object(dispatch, "launch") as launch:
            yield project, planned, launch


def test_next_two_ready() -> None:
    with next_fixture() as (project, planned, launch), contextlib.redirect_stdout(io.StringIO()) as out:
        planned("TASK-002", "b.py")
        planned("TASK-001")
        dispatch.dispatch_next(project, 2)
        assert [c.args[1] for c in launch.call_args_list] == ["TASK-001", "TASK-002"]
        for call in launch.call_args_list:
            _, tid, role, argv = call.args
            assert role == "omi-agent-engineer"
            assert argv == [sys.executable, "-m", "omi", "run", role, tid,
                            "--tool", "codex", "--model", "task-model", "--effort", "high"]
            wt = project.code.parent / "code.wt" / tid
            assert wt.exists()
            meta = dispatch.core.meta(wt / ".omi/tasks" / f"{tid}.md")
            assert meta["status"] == "in-progress" and meta["step"] == "build"
            assert "plan skipped" in meta["_text"]
            assert "dispatch next: task file has scope, skills and criteria" in meta["_text"]
            assert dispatch.core.git(wt, "status", "--porcelain") == ""
        assert "nothing ready" not in out.getvalue()


def test_next_conflicts_and_dependencies() -> None:
    with next_fixture() as (project, planned, launch), contextlib.redirect_stdout(io.StringIO()) as out:
        planned("TASK-001", "busy/x.py")
        planned("TASK-002", "free/**")
        planned("TASK-003", "free/x.py")
        planned("TASK-004", "other.py", "depends: TASK-999\n")
        planned("TASK-005", "last.py")
        planned("TASK-900", "busy/**", "depends: TASK-005\n")
        path = project.state / ".omi/tasks/TASK-900.md"
        path.write_text(path.read_text(encoding="utf-8").replace("status: planned", "status: in-progress"), encoding="utf-8")
        with patch.object(dispatch, "records", return_value=[{"tid": "TASK-900", "running": True}]):
            dispatch.dispatch_next(project, 3)
        assert [c.args[1] for c in launch.call_args_list] == ["TASK-002"]
        output = out.getvalue()
        assert "skip TASK-001:" in output and "scopes overlap" in output
        assert "skip TASK-003:" in output
        assert "skip TASK-004:" in output and "TASK-999" in output
        assert "skip TASK-005:" in output and "depends on TASK-005" in output


def test_next_readiness_and_limit() -> None:
    with next_fixture() as (project, planned, launch), contextlib.redirect_stdout(io.StringIO()) as out:
        planned("TASK-001", "")
        planned("TASK-002", extra="skills: missing-skill\n")
        planned("TASK-003")
        planned("TASK-004", "b.py")
        dispatch.dispatch_next(project)
        assert [c.args[1] for c in launch.call_args_list] == ["TASK-003"]
        output = out.getvalue()
        assert "skip TASK-001:" in output and "scope" in output
        assert "skip TASK-002:" in output and "missing-skill" in output
        assert "skip TASK-004:" in output and "max" in output


def test_next_nothing_ready() -> None:
    with next_fixture() as (project, planned, launch), contextlib.redirect_stdout(io.StringIO()) as out:
        planned("TASK-001", extra="depends: TASK-999\n")
        dispatch.dispatch_next(project)
        launch.assert_not_called()
        assert out.getvalue().endswith("dispatch next: nothing ready\n")


def test_next_failure_stops() -> None:
    with next_fixture() as (project, planned, launch), contextlib.redirect_stdout(io.StringIO()):
        planned("TASK-001")
        second = planned("TASK-002", "b.py")
        launch.side_effect = state.StateError("launch failed")
        try:
            dispatch.dispatch_next(project, 2)
        except state.StateError as exc:
            assert "launch failed" in str(exc)
        else:
            raise AssertionError("failure swallowed")
        assert launch.call_count == 1
        assert dispatch.core.meta(second)["status"] == "planned"


def test_next_existing_worktree_and_done_dependency() -> None:
    with next_fixture() as (project, planned, launch), contextlib.redirect_stdout(io.StringIO()):
        planned("TASK-001", extra="depends: TASK-000\n")
        dep = planned("TASK-000", "other.py")
        dep.write_text(dep.read_text(encoding="utf-8").replace("status: planned", "status: done"), encoding="utf-8")
        helpers.git(project.code, "add", ".")
        helpers.git(project.code, "commit", "-qm", "tasks")
        wt = project.code.parent / "existing"
        helpers.git(project.code, "worktree", "add", str(wt), "-b", "task/TASK-001", "development")
        dispatch.dispatch_next(project)
        assert launch.call_count == 1
        assert dispatch.core.meta(wt / ".omi/tasks/TASK-001.md")["step"] == "build"


def test_next_detached_state() -> None:
    with helpers.detached_project() as (code, catalog, _, task), contextlib.redirect_stdout(io.StringIO()):
        home, _, _ = helpers.state_remote(catalog)
        tid = "TASK-098"
        target = task.with_name(f"{tid}.md")
        target.write_text("---\nid: TASK-098\nstatus: planned\nscope: other.py\n"
                          "tool: codex\nmodel: detached-model\neffort: medium\n---\n"
                          "## Acceptance criteria\n- [ ] works\n\n## Checkpoint\nDone:\n", encoding="utf-8")
        project = state.resolve(code)
        with patch.object(dispatch, "records", return_value=[]), patch.object(dispatch, "launch") as launch:
            dispatch.dispatch_next(project)
        launch.assert_called_once()
        assert launch.call_args.args[1] == tid
        assert dispatch.core.meta(target)["status"] == "in-progress"
        assert dispatch.core.meta(target)["step"] == "build"
        assert dispatch.core.git(home, "status", "--porcelain", "--", str(target)) == ""
        assert (code.parent / "code.wt" / tid).exists()
        assert not (code.parent / "code.wt" / tid / ".omi").exists()


def test_next_container_skipped() -> None:
    with next_fixture() as (project, planned, launch), contextlib.redirect_stdout(io.StringIO()) as out:
        planned("TASK-001", extra="type: epic\n")
        planned("TASK-002", "b.py", "parent: TASK-001\n")
        dispatch.dispatch_next(project)
        assert "skip TASK-001: has child tasks" in out.getvalue()
        assert [c.args[1] for c in launch.call_args_list] == ["TASK-002"]


def test_next_setup_failure_stops() -> None:
    for stage in ("commit", "worktree"):
        with next_fixture() as (project, planned, launch), contextlib.redirect_stdout(io.StringIO()):
            planned("TASK-001")
            second = planned("TASK-002", "b.py")
            original = dispatch.core.git
            def fail_worktree(root, *args):
                return None if args[:2] == ("worktree", "add") else original(root, *args)
            target = patch.object(dispatch.state_sync, "commit", side_effect=state.StateError("commit failed")) if stage == "commit" else \
                patch.object(dispatch.core, "git", side_effect=fail_worktree)
            with target:
                try:
                    dispatch.dispatch_next(project, 2)
                except state.StateError as exc:
                    assert stage in str(exc)
                else:
                    raise AssertionError(f"{stage} failure swallowed")
            launch.assert_not_called()
            assert dispatch.core.meta(second)["status"] == "planned"


def main():
    test_next_container_skipped()
    test_next_setup_failure_stops()
    test_next_detached_state()
    test_next_two_ready()
    test_next_conflicts_and_dependencies()
    test_next_readiness_and_limit()
    test_next_nothing_ready()
    test_next_failure_stops()
    test_next_existing_worktree_and_done_dependency()
    test_records_sort_across_roles()
    test_windows_launch_uses_spawner()
    test_windows_launch_waits_for_wrapper()
    test_posix_launch_stays_direct()
    test_windows_spawner_failure_propagates()
    test_windows_launch_breaks_away()
    test_windows_launch_breakaway_denied()
    test_windows_launch_errors_propagate()
    test_watch_windows_termination_codes()
    test_two_runs_finish_together()
    test_lost_wrapper_and_exit_codes()
    test_needs_scope_over_hook_failure()
    test_record_before_wrapper_starts()
    test_watch_round_limit()
    test_reviewer_next_action()


if __name__ == "__main__":
    main()
