"""Runs every area test file: python tests/test_omi.py [--jobs N] [--profile] (--jobs 1: one process, the old serial run)
OMI_QUIET=1: print only failures and a one-line summary; the full output goes to $OMI_RUN_DIR/test-output.log (else .omi-cache/)."""
import concurrent.futures
import contextlib
import io
import json
import os
import subprocess
import sys
import time
import tempfile
import traceback
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import helpers  # noqa: F401
import test_upgrade
import test_init
import test_github
import test_worker
import test_creds
import test_tools
import test_hooks
import test_tasks
import test_content
import test_cli
import test_attach
import test_detached
import test_install
import test_board
import test_board_server
import test_board_web
import test_structure
import test_dispatch
import test_accept
import test_advance

from omi.project import tasks
from omi.setup import upgrade
import omi.common.core


def report_failure(exc_type, exc, tb):
    """Print the traceback, then one `FAILED <test> <file>:<line> <exception>` line naming the innermost test_* frame."""
    sys.__excepthook__(exc_type, exc, tb)
    frames = [(f.f_code.co_name, f.f_code.co_filename, n) for f, n in traceback.walk_tb(tb)] or [("?", "?", 0)]
    name, filename, lineno = next((f for f in reversed(frames) if f[0].startswith("test_")), frames[-1])  # else the innermost frame
    print(f"FAILED {name} {filename}:{lineno} {exc_type.__name__}: {exc}".replace("\n", " "), file=sys.stderr, flush=True)


def track_calls(modules, skips=None, times=None):
    """Record test calls, printed skips and (times) each test's wall time, silencing only implicit fixture output."""
    skips = [] if skips is None else skips
    times = {} if times is None else times
    defined, called = set(), set()
    for mod in modules:
        for name, fn in list(vars(mod).items()):
            if name.startswith("test_") and callable(fn) and getattr(fn, "__module__", None) == mod.__name__:
                key = (mod.__name__, name)
                defined.add(key)
                def wrapper(*a, _fn=fn, _key=key, **kw):
                    called.add(_key)
                    out = io.StringIO()
                    # omi.app.cli.main reconfigures stdout to UTF-8; StringIO already stores Unicode.
                    out.reconfigure = lambda **kw: None
                    start = time.perf_counter()
                    try:
                        with contextlib.redirect_stdout(out), helpers.quiet_fixtures():
                            return _fn(*a, **kw)
                    finally:
                        times[f"{_key[0]}.{_key[1]}"] = times.get(f"{_key[0]}.{_key[1]}", 0) + time.perf_counter() - start
                        text = out.getvalue()
                        for line in text.splitlines():
                            if line.lower().startswith("skip "):
                                label, sep, reason = line[5:].partition(": ")
                                label = label if label.startswith("test_") else _key[1]
                                skips.append(f"{label} ({reason})" if sep else label)
                        sys.stdout.write(text)
                setattr(mod, name, wrapper)
    return defined, called


def check_test_modules(root: Path, modules: list) -> None:
    imported = {Path(m.__file__).resolve() for m in modules if getattr(m, "__file__", None)}
    missing = sorted(p.name for p in root.glob("test_*.py") if p.resolve() not in imported)
    assert not missing, f"test files never imported by the suite: {', '.join(missing)}"


def test_fixture_output_capture() -> None:
    with tempfile.TemporaryDirectory() as d, contextlib.redirect_stdout(io.StringIO()) as suite:
        with helpers.quiet_fixtures():
            upgrade.init(Path(d))
            upgrade.init(Path(d))
            upgrade.upgrade_apply(Path(d))
            assert suite.getvalue() == "", suite.getvalue()
            # Explicit captures still see the CLI's per-file output.
            with contextlib.redirect_stdout(io.StringIO()) as cli:
                upgrade.init(Path(d))
            assert "skip   AGENTS.md (exists)" in cli.getvalue()
            with contextlib.redirect_stdout(io.StringIO()) as cli:
                upgrade.upgrade_apply(Path(d))
            assert cli.getvalue(), "upgrade output assertions must still work"


def test_skip_summary() -> None:
    skips = []
    def test_missing_dependency():
        print("skip test_missing_dependency: dependency missing")
    def test_symlink():
        print("skip symlink fixture: symlink creation unavailable")
    def test_missing_shell():
        print("SKIP test_missing_shell: no sh on PATH or in Git for Windows")
    for fn in (test_missing_dependency, test_symlink, test_missing_shell):
        fn.__module__ = "fake_tests"
    mod = SimpleNamespace(__name__="fake_tests", test_missing_dependency=test_missing_dependency,
                          test_symlink=test_symlink, test_missing_shell=test_missing_shell)
    with contextlib.redirect_stdout(io.StringIO()):
        defined, called = track_calls([mod], skips)
        mod.test_missing_dependency()
        mod.test_symlink()
        mod.test_missing_shell()
    assert defined == called
    # A nested test may run while its caller checks the exact print calls.
    with patch("builtins.print") as printed:
        mod.test_missing_dependency()
    printed.assert_called_once_with("skip test_missing_dependency: dependency missing")
    assert skips == [
        "test_missing_dependency (dependency missing)",
        "test_symlink (symlink creation unavailable)",
        "test_missing_shell (no sh on PATH or in Git for Windows)",
    ]


def test_unimported_test_file() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        runner = root / "test_omi.py"
        known = root / "test_known.py"
        omitted = root / "test_omitted.py"
        for path in (runner, known, omitted):
            path.write_text("def main(): pass\n", encoding="utf-8")
        modules = [SimpleNamespace(__file__=str(runner)), SimpleNamespace(__file__=str(known))]
        try:
            check_test_modules(root, modules)
        except AssertionError as exc:
            assert "test_omitted.py" in str(exc), exc
        else:
            raise AssertionError("unimported test file passed the suite guard")
        omitted.unlink()
        check_test_modules(root, modules)


def test_release_0_6_0():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "git+https://github.com/omi-teams/omi@v0.6.0" in readme
    assert "omi --version             # omi 0.6.0" in readme
    assert omi.common.core.version() == "0.6.0"
    assert upgrade.template_shas() == json.loads(upgrade.SHAS.read_text(encoding="utf-8"))["0.6.0"]


def test_phase():
    wf = [{"id": "plan", "role": "coordinator"}, {"id": "design", "role": "omi-agent-architect"},
          {"id": "build", "role": "omi-agent-engineer"}, {"id": "docs", "role": "omi-agent-docs-writer"},
          {"id": "ops", "role": "omi-agent-devops"}, {"id": "ui", "role": "omi-agent-designer-ui"},
          {"id": "res", "role": "omi-agent-researcher"}, {"id": "review", "role": "omi-agent-reviewer"},
          {"id": "sec", "role": "omi-agent-security-reviewer"}, {"id": "qa", "role": "omi-agent-qa-tester"},
          {"id": "odd", "role": "mystery"}, {"id": "accept", "role": "coordinator", "gate": "po"}]
    ph = lambda status, step, steps=wf, text="": tasks.phase({"status": status, "step": step, "_text": text}, steps)
    assert ph("planned", "build")["label"] == "Chưa bắt đầu" and ph("planned", "build")["key"] == "not_started"
    assert ph("blocked", "build")["label"] == "Bị chặn" and ph("done", "accept")["label"] == "Xong"
    for step, key, label in (("accept", "po", "Chờ PO"), ("plan", "planning", "Lên kế hoạch"), ("design", "design", "Thiết kế"),
                             ("ui", "design", "Thiết kế"), ("res", "design", "Thiết kế"), ("build", "working", "Đang làm"),
                             ("docs", "working", "Đang làm"), ("ops", "working", "Đang làm"), ("review", "review", "Đang review"),
                             ("sec", "review", "Đang review"), ("qa", "qa", "Đang QA"), ("odd", "working", "Đang làm"),
                             ("", "working", "Đang làm"), ("nope", "working", "Đang làm")):
        got = ph("in-progress", step)
        assert (got["key"], got["label"]) == (key, label), (step, got)
    assert ph("in-progress", "build", [])["label"] == "Đang làm" and ph("in-progress", "build", [])["step_count"] == 0
    got = ph("in-progress", "review")
    assert (got["step_index"], got["step_count"], got["step"]) == (8, 12, "review") and got["review_round"] == 1
    assert ph("in-progress", "build")["review_round"] is None
    usage = ("\n## Usage\n| role | model | effort | input | output | cache | duration | skills read | verdict |\n|---|---|---|---|---|---|---|---|---|\n"
             "| omi-agent-reviewer | m | high | 1 | 1 | 1 | 1s | - | FAIL abc1234 |\n"
             "| omi-agent-reviewer | m | high | 1 | 1 | 1 | 1s | - | QUOTA->x |\n"
             "| omi-agent-engineer | m | high | 1 | 1 | 1 | 1s | - | FAIL |\n"
             "| omi-agent-reviewer | m | high | 1 | 1 | 1 | 1s | - | PASS |\n")
    assert ph("in-progress", "review", text=usage)["review_round"] == 2
    assert ph("in-progress", "qa", text=usage)["review_round"] == 2
    m = {"status": "in-progress", "step": "design", "_text": ""}
    assert tasks.step_strip(m, wf[:4]) == "plan ✓ [design] build docs"
    assert tasks.step_strip({**m, "status": "done"}, wf[:2]) == "plan ✓ design ✓"


MODULES = [test_upgrade, test_init, test_github, test_worker, test_creds, test_tools, test_hooks, test_tasks, test_content,
           test_cli, test_attach, test_detached, test_install, test_board, test_board_server, test_board_web, test_structure,
           test_dispatch, test_advance, test_accept]
RESULT = "OMI-SUITE-RESULT: "


def run_modules(mods, skips, times):
    """Run each module's main() in this process; fail when a defined test was never called."""
    defined, called = track_calls(mods, skips, times)
    for mod in mods:
        mod.main()
    skipped = sorted(f"{mod}.{name}" for mod, name in defined - called)
    assert not skipped, f"test functions never called by a main(): {', '.join(skipped)}"


def run_child(name):
    """One module in its own process (--only): prints its output, then one result line for the parent."""
    skips, times = [], {}
    run_modules([sys.modules[name]], skips, times)
    print(RESULT + json.dumps({"skips": skips, "times": times}), flush=True)


def run_parallel(mods, jobs, skips, times):
    """Each module in a child process, `jobs` at a time; output is printed per module once it finishes. Returns failed module names."""
    def one(mod):
        start = time.perf_counter()
        r = subprocess.run([sys.executable, __file__, "--only", mod.__name__], cwd=Path(__file__).parent.parent,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        return mod.__name__, r, time.perf_counter() - start
    failed = []
    with concurrent.futures.ThreadPoolExecutor(jobs) as pool:
        for name, r, took in pool.map(one, mods):
            out, _, result = r.stdout.rpartition(RESULT)
            if r.returncode or not result:
                failed.append(name)
                sys.stdout.write(r.stdout + r.stderr)
                print(f"FAILED module {name} (exit {r.returncode}, {took:.1f}s)", flush=True)
                continue
            sys.stdout.write(out)
            data = json.loads(result)
            skips += data["skips"]
            times.update(data["times"])
            times[f"{name} (process)"] = took
    return failed


def quiet(argv, log):
    """Run argv with its full output in `log`; print only the failure lines and one summary line. Returns its exit code."""
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.touch()
    except OSError:  # read-only worktree (review container)
        log = Path(tempfile.gettempdir()) / "omi-test-output.log"
    start = time.perf_counter()
    with log.open("w", encoding="utf-8", newline="\n") as out:
        code = subprocess.run(argv, stdout=out, stderr=subprocess.STDOUT, env={k: v for k, v in os.environ.items() if k != "OMI_QUIET"}).returncode
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    failed = [l for l in lines if l.startswith("FAILED")]
    if code:
        print("\n".join(failed or lines[-20:]))
    print(f"tests: {'FAILED' if code else 'ok'} ({len(failed)} failure lines, {time.perf_counter() - start:.0f}s; full output: {log})", flush=True)
    return code


def test_quiet() -> None:
    with tempfile.TemporaryDirectory() as d:
        log = Path(d) / "run" / "test-output.log"
        script = "import sys; print('noise\\n' * 50 + 'FAILED test_x a.py:1 AssertionError: boom'); sys.exit(1)"
        with contextlib.redirect_stdout(io.StringIO()) as shown:
            assert quiet([sys.executable, "-c", script], log) == 1
        assert shown.getvalue().splitlines()[0] == "FAILED test_x a.py:1 AssertionError: boom", shown.getvalue()
        assert "noise" not in shown.getvalue() and len(shown.getvalue().splitlines()) == 2
        assert shown.getvalue().splitlines()[-1].startswith("tests: FAILED (1 failure lines")
        assert log.read_text(encoding="utf-8").count("noise") == 50
        with contextlib.redirect_stdout(io.StringIO()) as shown:
            assert quiet([sys.executable, "-c", "print('all fine')"], log) == 0
        assert shown.getvalue().startswith("tests: ok (0 failure lines") and len(shown.getvalue().splitlines()) == 1
        assert log.read_text(encoding="utf-8") == "all fine\n"


def options(argv):
    jobs, profile, only = os.cpu_count() or 1, "--profile" in argv, None
    if "--jobs" in argv:
        jobs = max(1, int(argv[argv.index("--jobs") + 1]))
    if "--only" in argv:
        only = argv[argv.index("--only") + 1]
    return jobs, profile, only


def test_options() -> None:
    assert options(["--jobs", "3", "--profile"]) == (3, True, None)
    assert options(["--jobs", "0"])[0] == 1 and options([])[0] == (os.cpu_count() or 1)
    assert options(["--only", "test_tasks"])[2] == "test_tasks"


if __name__ == "__main__":
    sys.excepthook = report_failure
    jobs, profile, only = options(sys.argv[1:])
    if only:
        run_child(only)
        sys.exit(0)
    if os.environ.get("OMI_QUIET") == "1":
        run_dir = os.environ.get("OMI_RUN_DIR") or Path(__file__).parent.parent / ".omi-cache"
        sys.exit(quiet([sys.executable, __file__, *sys.argv[1:]], Path(run_dir) / "test-output.log"))
    check_test_modules(Path(__file__).parent, list(sys.modules.values()))
    real_skips, times = [], {}
    own = sys.modules[__name__]
    own_defined, own_called = track_calls([own], real_skips, times)
    test_fixture_output_capture()
    test_skip_summary()
    test_unimported_test_file()
    test_phase()
    test_release_0_6_0()
    test_options()
    test_quiet()
    assert {m.__name__ for m in MODULES} | {"test_omi"} == {p.stem for p in Path(__file__).parent.glob("test_*.py")}, "MODULES must list every test file"
    if jobs == 1:
        run_modules(MODULES, real_skips, times)
    elif failed := run_parallel(MODULES, jobs, real_skips, times):
        sys.exit(f"FAILED modules: {', '.join(failed)}")
    assert own_defined == own_called, f"runner tests never called: {sorted(own_defined - own_called)}"
    if profile:
        print("slowest tests:")
        for name, took in sorted(((n, s) for n, s in times.items() if not n.endswith("(process)")), key=lambda x: -x[1])[:20]:
            print(f"  {took:6.2f}s {name}")
        print("module processes: " + ", ".join(f"{n.split()[0]} {s:.0f}s" for n, s in sorted(
            ((n, s) for n, s in times.items() if n.endswith("(process)")), key=lambda x: -x[1])[:8]))
    print("skipped: " + ("; ".join(real_skips) if real_skips else "none"))
    print("ok")
