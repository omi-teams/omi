"""Runs every area test file in one process: python tests/test_omi.py"""
import contextlib
import io
import json
import sys
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

from omi.project import tasks
from omi.setup import upgrade
import omi.common.core


def report_failure(exc_type, exc, tb):
    """Print the traceback, then one `FAILED <test> <file>:<line> <exception>` line naming the innermost test_* frame."""
    sys.__excepthook__(exc_type, exc, tb)
    frames = [(f.f_code.co_name, f.f_code.co_filename, n) for f, n in traceback.walk_tb(tb)] or [("?", "?", 0)]
    name, filename, lineno = next((f for f in reversed(frames) if f[0].startswith("test_")), frames[-1])  # else the innermost frame
    print(f"FAILED {name} {filename}:{lineno} {exc_type.__name__}: {exc}".replace("\n", " "), file=sys.stderr, flush=True)


def track_calls(modules, skips=None):
    """Record test calls and printed skips, silencing only implicit fixture output."""
    skips = [] if skips is None else skips
    defined, called = set(), set()
    for mod in modules:
        for name, fn in list(vars(mod).items()):
            if name.startswith("test_") and callable(fn) and getattr(fn, "__module__", None) == mod.__name__:
                key = (mod.__name__, name)
                defined.add(key)
                def wrapper(*a, _fn=fn, _key=key, **kw):
                    called.add(_key)
                    out = io.StringIO()
                    out.reconfigure = lambda **kw: None
                    try:
                        with contextlib.redirect_stdout(out), helpers.quiet_fixtures():
                            return _fn(*a, **kw)
                    finally:
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


def report_success(skips: list[str]) -> None:
    print("skipped: " + ("; ".join(skips) if skips else "none"))
    print("ok")


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
    with contextlib.redirect_stdout(io.StringIO()) as out:
        report_success(skips)
    assert out.getvalue().splitlines() == [
        "skipped: test_missing_dependency (dependency missing); test_symlink (symlink creation unavailable); "
        "test_missing_shell (no sh on PATH or in Git for Windows)", "ok"]
    with contextlib.redirect_stdout(io.StringIO()) as out:
        report_success([])
    assert out.getvalue() == "skipped: none\nok\n"


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


def test_release_0_5_0():
    assert omi.common.core.version() == "0.5.0"
    assert upgrade.template_shas() == json.loads(upgrade.SHAS.read_text(encoding="utf-8"))["0.5.0"]


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


if __name__ == "__main__":
    sys.excepthook = report_failure
    check_test_modules(Path(__file__).parent, list(sys.modules.values()))
    real_skips = []
    defined, called = track_calls([m for m in list(sys.modules.values()) if getattr(m, "__file__", None)
                                   and Path(m.__file__).parent == Path(__file__).parent and Path(m.__file__).name.startswith("test_")], real_skips)
    test_fixture_output_capture()
    test_skip_summary()
    test_unimported_test_file()
    test_phase()
    test_release_0_5_0()
    test_upgrade.main()
    test_init.main()
    test_github.main()
    test_worker.main()
    test_creds.main()
    test_tools.main()
    test_hooks.main()
    test_tasks.main()
    test_content.main()
    test_cli.main()
    test_attach.main()
    test_detached.main()
    test_install.main()
    test_board.main()
    test_board_server.main()
    test_board_web.main()
    test_structure.main()
    test_dispatch.main()
    skipped = sorted(f"{mod}.{name}" for mod, name in defined - called)
    assert not skipped, f"test functions never called by a main(): {', '.join(skipped)}"
    report_success(real_skips)
