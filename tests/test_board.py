"""Board data contracts, read-only behavior and state path boundaries."""
import json
import os
import subprocess
import tempfile
import threading
import time
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import helpers
from helpers import git
from omi.board import data, source, timeline


@contextmanager
def state_dir(env=True):
    """Temp state home; waits for background fetches before removal (Windows cannot delete a busy dir)."""
    with tempfile.TemporaryDirectory() as directory:
        try:
            with patch.dict(os.environ, {"OMI_STATE": directory} if env else {}):
                yield directory
        finally:
            source.wait_fetches()


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def fixture(home):
    root = home / "projects" / "sample"
    write(root / ".omi/plans/PLAN-001.md", "---\nid: PLAN-001\ntitle: Plan\nstatus: active\n---\n")
    write(root / ".omi/workflows/feature.md", "---\nsteps:\n- id: accept | gate: po\n---\n")
    for id, status, extra in (("TASK-001", "done", ""), ("TASK-002", "in-progress", "step: accept\nworkflow: feature\n"),
                              ("TASK-003", "blocked", ""), ("TASK-004", "planned", "depends: TASK-001\n"),
                              ("TASK-005", "planned", "depends: TASK-003\n")):
        write(root / f".omi/tasks/{id}.md", f"---\nid: {id}\ntitle: <script>alert(1)</script>\nstatus: {status}\nplan: PLAN-001\n{extra}---\n"
              "## Goal\nShip it\n\n## Acceptance criteria\n- [x] one\n- [ ] two\n\n## Checkpoint\nDone: one\nNext: ask PO\n"
              "\n## Steps\n- accept started 2026-10-29 12:00\n\n## Reports\n- review 2026-10-29 13:00 took 12s\n\n## Usage\n"
              "| role | model | effort | input | output | cache | duration | skills read | verdict |\n"
              "|---|---|---|---|---|---|---|---|---|\n"
              "| omi-agent-reviewer | model-a | high | 10 | 2 | n/a | 12s | - | PASS |\n"
              "| omi-agent-reviewer | model-a | high | n/a | 0 | 3 | 1s | - | QUOTA->other |\n")
    write(root / ".omi/decisions.md", "# Decisions\n- 2026-10-28 | old\n- 2026-10-29 | new\n")
    return root


def remote(home):
    git(home, "init", "-q", "-b", "main")
    origin = home / ".git" / "test-origin.git"
    origin.mkdir()
    git(origin, "init", "--bare", "-q", "-b", "main")
    git(home, "remote", "add", "origin", str(origin))
    publish(home)
    source._CACHE.clear()
    return origin


def settle():
    """Wait for the background fetch and drop the version cache so the next request sees its result."""
    source.wait_fetches()
    source._CACHE.clear()


def poll(home, call):
    """Expire the version cache and let the background fetch land; the second request sees its result."""
    for _ in range(2):
        with patch("omi.board.source.time.monotonic", return_value=source._CACHE[home][0] + 11):
            result = call()
        source.wait_fetches()
    return result


def publish(home):
    git(home, "add", ".")
    git(home, "commit", "-qm", "state update")
    git(home, "push", "-q", "origin", "main")
    source._CACHE.clear()


def test_views():
    with state_dir() as directory:
        home = Path(directory)
        root = fixture(home)
        decisions = root / ".omi/decisions.md"
        write(decisions, decisions.read_text(encoding="utf-8") + f"- 2020-01-01 | old cache {home}\n")
        origin = remote(home)
        before = {f: f.read_bytes() for f in root.rglob("*") if f.is_file()}
        detail = data.task("sample", "TASK-002")
        assert detail["goal"] == "Ship it"
        assert detail["frontmatter"]["title"].startswith("<script>")
        assert detail["criteria"] == [{"text": "one", "checked": True}, {"text": "two", "checked": False}]
        assert "Next: ask PO" in detail["checkpoint"] and "accept started" in detail["steps"]
        assert "took 12s" in detail["reports"]
        assert detail["phase"] == {"key": "po", "label": "Chờ PO"} and (detail["step_index"], detail["step_count"], detail["review_round"]) == (1, 1, None)
        assert data.task("sample", "TASK-003")["phase"]["key"] == "blocked"
        assert detail["usage"]["input"] == 10 and detail["usage"]["review_rounds"] == 1
        settle()
        view = data.project("sample")
        assert view["plans"][0]["done"] == 1 and view["plans"][0]["total"] == 5
        assert view["task_counts"] == {"planned": 2, "in-progress": 1, "blocked": 1, "review": 0, "done": 1}
        assert {(w["id"], w["reason"]) for w in view["po_waiting"]} == {
            ("TASK-002", "po_gate"), ("TASK-002", "next"), ("TASK-003", "blocked"), ("TASK-004", "next_task")}
        assert view["po_waiting_count"] == 3
        assert view["activity"][0]["time"] == "2026-10-29 13:00" and view["activity"][0]["duration"] == "12s"
        assert "new" in view["decisions"][0]
        assert view["usage"]["models"]["model-a"] == {"runs": 10, "input": 50, "output": 10, "cache": 15, "review_rounds": 5}
        assert view["source"]["stale"] is False and len(view["source"]["sha"]) == 40
        assert view["source"]["fetched_at"]
        assert "sync" not in view
        assert all("sync" not in p for p in data.projects()["projects"])
        assert data.projects()["projects"][0]["name"] == "sample"
        for response in (detail, view, data.projects()):
            assert str(home) not in json.dumps(response)
        assert before == {f: f.read_bytes() for f in root.rglob("*") if f.is_file()}
        path = root / ".omi/tasks/TASK-002.md"
        write(path, path.read_text(encoding="utf-8").replace("Ship it", "Uncommitted"))
        assert data.task("sample", "TASK-002")["goal"] == "Ship it"
        git(home, "add", ".")
        git(home, "commit", "-qm", "unpushed")
        source._CACHE.clear()
        assert data.task("sample", "TASK-002")["goal"] == "Ship it"
        source.wait_fetches()  # a running background fetch must not race the repo change
        git(home, "push", "-q", "origin", "main")
        source._CACHE.clear()
        pushed = data.task("sample", "TASK-002")
        assert pushed["goal"] == "Uncommitted" and pushed["source"]["sha"] != detail["source"]["sha"]
        # Another checkout pushes without updating this cache's remote-tracking ref.
        producer = home / ".git" / "producer"
        git(home, "clone", "-q", str(origin), str(producer))
        remote_path = producer / "projects/sample/.omi/tasks/TASK-002.md"
        write(remote_path, remote_path.read_text(encoding="utf-8").replace("Uncommitted", "Pushed elsewhere"))
        old_sha = pushed["source"]["sha"]
        publish(producer)
        assert data.core.git(home, "rev-parse", "origin/main") == old_sha
        data.task("sample", "TASK-002")
        settle()
        pushed = data.task("sample", "TASK-002")
        assert pushed["goal"] == "Pushed elsewhere" and pushed["source"]["sha"] != old_sha
        # Neither successful nor failed fetch alters HEAD, index or local files.
        write(path, "local dirty data")
        head = data.core.git(home, "rev-parse", "HEAD")
        status = data.core.git(home, "status", "--porcelain")
        assert poll(home, lambda: data.task("sample", "TASK-002"))["goal"] == pushed["goal"]
        assert path.read_text(encoding="utf-8") == "local dirty data"
        assert data.core.git(home, "rev-parse", "HEAD") == head
        assert data.core.git(home, "status", "--porcelain") == status
        pushed = poll(home, lambda: data.task("sample", "TASK-002"))
        landed = source._FETCHES[home]["at"]
        source.wait_fetches()  # a running background fetch must not race the repo change
        git(home, "remote", "set-url", "origin", str(origin / "unavailable"))
        stale = poll(home, lambda: data.task("sample", "TASK-002"))
        assert stale["goal"] == pushed["goal"]
        assert stale["source"]["stale"] is True
        assert stale["source"]["fetched_at"] == landed
        assert stale["source"]["sha"] == pushed["source"]["sha"]
        assert path.read_text(encoding="utf-8") == "local dirty data"
        assert data.core.git(home, "rev-parse", "HEAD") == head
        assert data.core.git(home, "status", "--porcelain") == status
        source.wait_fetches()  # a running background fetch must not race the repo change
        git(home, "remote", "set-url", "origin", str(origin))
        assert poll(home, lambda: data.task("sample", "TASK-002"))["source"]["stale"] is False


def test_plan_status_derived():
    with state_dir() as directory:
        home = Path(directory)
        root = home / "projects" / "sample"
        for pid, stored in (("PLAN-001", "active"), ("PLAN-002", "active"), ("PLAN-003", "active"), ("PLAN-004", "done")):
            write(root / f".omi/plans/{pid}.md", f"---\nid: {pid}\ntitle: P\nstatus: {stored}\n---\n")
        for tid, plan, status in (("TASK-001", "PLAN-001", "done"), ("TASK-002", "PLAN-001", "done"),
                                  ("TASK-003", "PLAN-002", "done"), ("TASK-004", "PLAN-002", "planned")):
            write(root / f".omi/tasks/{tid}.md", f"---\nid: {tid}\ntitle: T\nstatus: {status}\nplan: {plan}\n---\n")
        remote(home)
        shown = {p["id"]: p["status"] for p in data.project("sample")["plans"]}
        assert shown == {"PLAN-001": "done", "PLAN-002": "active", "PLAN-003": "active", "PLAN-004": "done"}
        assert [p["id"] for p in data.projects()["projects"][0]["plans"]] == ["PLAN-002", "PLAN-003"]
        assert "status: active" in (root / ".omi/plans/PLAN-001.md").read_text(encoding="utf-8")


def test_hierarchy():
    with state_dir() as directory:
        home = Path(directory)
        root = home / "projects" / "sample"
        for tid, extra in (("TASK-001", "type: milestone\nstatus: planned\n"), ("TASK-002", "type: epic\nparent: TASK-001\nstatus: planned\n"),
                           ("TASK-003", "parent: TASK-002\nstatus: done\n"), ("TASK-004", "parent: TASK-002\nstatus: blocked\n"),
                           ("TASK-005", "parent: TASK-001\nstatus: planned\n")):
            write(root / f".omi/tasks/{tid}.md", f"---\nid: {tid}\ntitle: T\n{extra}---\n")
        remote(home)
        view = data.project("sample")
        got = {t["id"]: (t["type"], t["parent"], t["children"], t["status"]) for items in view["kanban"].values() for t in items}
        assert got == {"TASK-001": ("milestone", None, ["TASK-002", "TASK-005"], "blocked"),
                       "TASK-002": ("epic", "TASK-001", ["TASK-003", "TASK-004"], "blocked"),
                       "TASK-003": ("task", "TASK-002", [], "done"), "TASK-004": ("task", "TASK-002", [], "blocked"),
                       "TASK-005": ("task", "TASK-001", [], "planned")}, got
        assert {t["id"] for t in view["kanban"]["blocked"]} == {"TASK-001", "TASK-002", "TASK-004"}
        assert [w["id"] for w in view["po_waiting"] if w["reason"] == "next_task"] == ["TASK-005"]


def test_shared_fetch():
    with state_dir() as directory:
        home = Path(directory)
        fixture(home)
        remote(home)
        real_git, real_fetch = source.core.git, source._fetch
        with patch("omi.board.source.core.git", wraps=real_git) as calls, patch("omi.board.source._fetch", side_effect=lambda h: (time.sleep(0.5), real_fetch(h))[1]) as fetches, \
                patch("omi.board.source.time.monotonic", return_value=100):
            with ThreadPoolExecutor(max_workers=6) as pool:
                views = list(pool.map(lambda _: data.projects(), range(12)))
            assert all(v["source"] == views[0]["source"] for v in views)
            source.wait_fetches()  # tests schedule the background fetch: join before every count
            assert fetches.call_count == 1
            with patch("omi.board.source.time.monotonic", return_value=101):
                data.projects()
            source.wait_fetches()
            assert fetches.call_count == 1
            with patch("omi.board.source.time.monotonic", return_value=102):
                data.projects()
            source.wait_fetches()
            assert fetches.call_count == 2
            assert {c.args[1] for c in calls.call_args_list} <= {"rev-parse", "remote", "ls-tree", "show"}
        for url, expected in (("https://user:token@github.com/omi-teams/omi-state?token=secret", "https://github.com/omi-teams/omi-state"),
                              ("git@github.com:omi-teams/omi-state.git", "github.com:omi-teams/omi-state.git"),
                              ("ssh://git@github.com:2222/omi-teams/omi-state.git", "ssh://github.com:2222/omi-teams/omi-state.git"),
                              (str(home), ""), (r"C:\x\y", ""), ("C:/x/y", ""), ("file:///local/state", "")):
            assert source._repo(url) == expected


def test_version() -> None:
    with state_dir() as directory:
        home = Path(directory)
        root = fixture(home)
        remote(home)
        real_git = source.core.git
        with patch("omi.board.source.Snapshot", side_effect=AssertionError("snapshot parsed")), \
                patch("omi.board.source.core.git", wraps=real_git) as calls:
            first = data.version()
            assert first["sha"] == data.version("sample")["sha"]
            assert {c.args[1] for c in calls.call_args_list} <= {"rev-parse", "remote", "ls-tree"}
        path = root / ".omi/tasks/TASK-002.md"
        write(path, "changed state")
        assert data.version()["sha"] == first["sha"]
        git(home, "add", ".")
        git(home, "commit", "-qm", "local change")
        source._CACHE.clear()
        assert data.version()["sha"] == first["sha"]
        source.wait_fetches()  # a running background fetch must not race the repo change
        git(home, "push", "-q", "origin", "main")
        # Version and full data share the same fetch cache and expiry.
        assert data.version()["sha"] == first["sha"]
        with patch("omi.board.source.time.monotonic", return_value=source._CACHE[home][0] + 3):
            pushed = data.version("sample")
        assert pushed["sha"] != first["sha"]
        assert pushed["sha"] == data.project("sample")["source"]["sha"]
        for name in ("..", "../sample", "x/y", "x\\y", "x:", "x\0"):
            refuses(lambda: data.version(name))
        try:
            data.version("missing")
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("missing project served")


def test_path_redaction() -> None:
    with state_dir(env=False) as directory:
        home = Path(directory) / "cache"
        home.mkdir()
        fixture(home)
        remote(home)
        # Different spelling without relying on symlink privileges.
        spelled = home / ".." / "cache"
        variants = {str(p).replace("\\", "/") for p in (spelled, spelled.resolve())}
        variants |= {p.replace("/", "\\") for p in variants}
        path = home / "projects/sample/.omi/tasks/TASK-002.md"
        write(path, path.read_text(encoding="utf-8").replace("Ship it", " | ".join(sorted(variants))))
        publish(home)
        with patch("omi.board.source.state.state_home", return_value=spelled):
            for response in (data.projects(), data.project("sample"), data.task("sample", "TASK-002")):
                encoded = json.dumps(response, ensure_ascii=False)
                for variant in variants:
                    assert json.dumps(variant)[1:-1] not in encoded
                if "projects" not in response:
                    assert "[state]" in encoded
            snap = source.snapshot()
            assert snap.response({v: [v] for v in variants})["[state]"] == ["[state]"]


def test_snapshot_one_git_process() -> None:
    with state_dir() as directory:
        home = Path(directory)
        fixture(home)
        remote(home)
        snap = source.snapshot()
        real_run, argvs = subprocess.run, []

        def spy(argv, *a, **kw):
            argvs.append(argv)
            return real_run(argv, *a, **kw)
        with patch("omi.common.core.subprocess.run", side_effect=spy):
            texts = {p: snap.read(p) for p in snap.paths}
        assert len(texts) > 5 and all(text for text in texts.values())
        assert len(argvs) == 1 and "cat-file" in argvs[0] and "--batch" in argvs[0], argvs
        # No new state commit: a later poll reads no blobs from git.
        source._CACHE.clear()
        with patch("omi.common.core.subprocess.run", side_effect=spy):
            again = source.snapshot()
            assert {p: again.read(p) for p in again.paths} == texts
        assert not any("cat-file" in a for a in argvs[1:]), argvs


def test_snapshot_load_hardened() -> None:
    with state_dir() as directory:
        home = Path(directory)
        fixture(home)
        remote(home)
        snap = source.snapshot()
        for effect in (subprocess.TimeoutExpired("git", 1), subprocess.CalledProcessError(1, "git")):
            with patch("omi.board.source.subprocess.run", side_effect=effect):
                try:
                    snap._load()
                    raise AssertionError("expected OSError")
                except OSError as exc:
                    assert str(exc) == "state file unavailable"
        for out in (b"abc blob 99\nshort\n", b"no newline"):
            with patch("omi.board.source.subprocess.run", return_value=subprocess.CompletedProcess([], 0, stdout=out)):
                try:
                    snap._load()
                    raise AssertionError("expected OSError")
                except OSError as exc:
                    assert str(exc) == "state file unavailable"


def test_newline_path_skipped() -> None:
    with state_dir() as directory:
        home = Path(directory)
        fixture(home)
        remote(home)
        # Windows cannot create such a file and Git for Windows rejects it in update-index, so build the tree with mktree.
        def out(*args, data=None):
            return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=home, input=data, check=True,
                                  capture_output=True).stdout
        blob = out("hash-object", "-w", "--stdin", data=b"x").decode().strip()
        tree = out("mktree", "-z", data=out("ls-tree", "-z", "HEAD") + f"100644 blob {blob}\tbad\nname.md\0".encode()).decode().strip()
        commit = out("commit-tree", tree, "-p", "HEAD", "-m", "newline path").decode().strip()
        out("reset", "--soft", commit)
        git(home, "push", "-q", "origin", "main")
        source._CACHE.clear()
        snap = source.snapshot()
        assert not any("\n" in str(p) for p in snap.paths)
        assert len(snap.paths) > 5 and all(snap.read(p) for p in snap.paths)


def test_request_does_not_wait_for_fetch() -> None:
    with state_dir() as directory:
        home = Path(directory)
        fixture(home)
        remote(home)
        release = threading.Event()
        with patch("omi.board.source._fetch", side_effect=lambda _: release.wait(10)):
            started = time.monotonic()
            view = data.projects()
            assert time.monotonic() - started < 5 and not release.is_set()
            assert view["source"]["stale"] is True and view["source"]["sha"]
            release.set()
            source._WORKERS[home].join()
        assert source._FETCHES[home]["ok"] is True


def test_projects_cached_per_commit_and_minute() -> None:
    with state_dir() as directory:
        home = Path(directory)
        fixture(home)
        remote(home)
        now = datetime(2026, 11, 3, 10, 30, 5)
        later = now.replace(minute=31)
        with patch("omi.board.data._now", return_value=now):
            first = data.projects()
            with patch("omi.board.data._detail", side_effect=AssertionError("parsed again")):
                assert data.projects()["projects"] == first["projects"]
        with patch("omi.board.data._now", return_value=later), \
                patch("omi.board.data._detail", wraps=data._detail) as details:
            data.projects()
            assert details.called


def test_unavailable_snapshot():
    with state_dir() as directory:
        source._CACHE.clear()
        with patch("omi.board.source.core.git", return_value=None), patch("omi.board.source._fetch", return_value=False) as fetches, \
                patch("omi.board.source.time.monotonic", return_value=100):
            for _ in range(2):
                try:
                    data.projects()
                except OSError as exc:
                    assert str(Path(directory)) not in str(exc)
                else:
                    raise AssertionError("missing origin/main served local content")
            assert fetches.call_count == 1


def test_fetch_timeout_serves_stale():
    with state_dir() as directory:
        home = Path(directory)
        fixture(home)
        remote(home)
        data.projects()
        fresh = poll(home, data.projects)["source"]
        landed = source._FETCHES[home]["at"]
        seen, real_run = [], subprocess.run

        def hang(argv, **kw):  # only the fetch hangs; other git calls still read the cache
            if "fetch" not in argv:
                return real_run(argv, **kw)
            seen.append((argv, kw))
            raise subprocess.TimeoutExpired(argv, kw["timeout"])
        with patch("omi.board.source.subprocess.run", side_effect=hang):
            stale = poll(home, data.projects)["source"]
        argv, kw = seen[0]
        assert "fetch" in argv and kw["env"]["GIT_TERMINAL_PROMPT"] == "0" and kw["timeout"] == source.FETCH_TIMEOUT
        assert kw["env"]["GCM_INTERACTIVE"] == "never" and kw["stdout"] == kw["stderr"] == subprocess.DEVNULL and "capture_output" not in kw
        assert stale["stale"] is True and stale["sha"] == fresh["sha"] and stale["fetched_at"] == landed


def test_workflow_detail():
    with state_dir() as directory:
        root = fixture(Path(directory))
        steps = [{"id": id, "gate": "po" if id == "accept" else "none"}
                 for id in ("plan", "design", "build", "review", "accept", "qa")]
        definition = "---\nsteps:\n" + "".join(f"- id: {s['id']} | gate: {s['gate']}\n" for s in steps) + "---\n"
        write(root / ".omi/workflows/feature.md", definition)
        remote(Path(directory))
        # The timeline is clock-based: pin the clock so both reads see the same running-step seconds.
        with patch.object(data, "_now", return_value=datetime(2026, 10, 29, 12, 5)):
            detail = data.task("sample", "TASK-002")
            assert detail["workflow_steps"] == steps and detail["current_step"] == "accept"
            card = data.project("sample")["kanban"]["in-progress"][0]
        assert {k: v for k, v in card.items() if k != "timeline"} == {k: v for k, v in detail.items() if k not in ("source", "timeline")}
        # Default, missing and changed definitions are read from state, never inferred from history.
        assert data.task("sample", "TASK-001")["workflow_steps"] == []
        write(root / ".omi/workflows/omi-flow-feature.md", definition)
        publish(Path(directory))
        assert data.task("sample", "TASK-001")["workflow_steps"] == steps
        assert data.task("sample", "TASK-001")["current_step"] is None
        write(root / ".omi/workflows/feature.md", "---\nsteps:\n- id: custom | gate: po\n---\n")
        publish(Path(directory))
        assert data.task("sample", "TASK-002")["workflow_steps"] == [{"id": "custom", "gate": "po"}]
        path = root / ".omi/tasks/TASK-002.md"
        write(path, path.read_text(encoding="utf-8").replace("workflow: feature", "workflow: ../../escape"))
        publish(Path(directory))
        refuses(lambda: data.task("sample", "TASK-002"))


def test_path_refusal():
    with state_dir() as directory:
        home = Path(directory)
        root = fixture(home)
        remote(home)
        for call in (lambda: data.project("../escape"), lambda: data.project("/absolute"),
                     lambda: data.task("sample", "../TASK-001"), lambda: data.task("sample", "x/y"),
                     lambda: data.project("."), lambda: data.task("sample", "x\\y")):
            refuses(call)
        # Tracked symlinks are never followed; local symlinks cannot affect the snapshot.
        target = root / ".omi/tasks/TASK-escape.md"
        try:
            target.symlink_to(home / "secret")
        except OSError:
            print("skip board snapshot symlink: symlink creation unavailable")
            return
        write(home / "secret", "must never be served")
        publish(home)
        assert "must never be served" not in json.dumps(data.project("sample"))
        target = root / ".omi/tasks/TASK-002.md"
        target.unlink()
        try:
            target.symlink_to(home / "secret")
        except OSError:
            print("skip board snapshot symlink: symlink creation unavailable")
            return
        assert data.task("sample", "TASK-002")["goal"] == "Ship it"


def test_snapshot_symlink_unavailable():
    with patch.object(Path, "symlink_to", side_effect=OSError("symlink creation unavailable")) as symlink, \
            patch("builtins.print") as printed:
        test_path_refusal()
    symlink.assert_called_once()
    printed.assert_called_once_with("skip board snapshot symlink: symlink creation unavailable")


def refuses(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError("unsafe path accepted")


def test_empty_and_layer():
    with state_dir() as directory:
        home = Path(directory)
        write(home / "README.md", "empty state")
        remote(home)
        assert data.projects()["projects"] == []
        write(home / "projects/empty/README.md", "empty project")
        publish(home)
        view = data.project("empty")
        assert view["plans"] == view["po_waiting"] == view["activity"] == view["decisions"] == []
        assert view["usage"]["totals"]["runs"] == 0
        assert str(home) not in json.dumps(view)


def usage_task(root, id, plan, tool, rows):
    table = "".join(f"| {r} |\n" for r in rows)
    write(root / f".omi/tasks/{id}.md", f"---\nid: {id}\ntitle: T {id}\nstatus: done\nplan: {plan}\ntool: {tool}\n---\n## Goal\nx\n\n## Usage\n"
          "| role | model | effort | input | output | cache | duration | skills read | verdict |\n|---|---|---|---|---|---|---|---|---|\n" + table)


def test_cost():
    with state_dir() as directory:
        home = Path(directory)
        root = home / "projects" / "sample"
        usage_task(root, "TASK-001", "PLAN-001", "claude", [
            "omi-agent-engineer | m-a | high | 1000000 | 500000 | 2000000 | 5s | - | -",
            "omi-agent-reviewer | m-a | high | 100 | 50 | n/a | 5s | - | FAIL abc1234",
            "omi-agent-reviewer | m-a | high | 100 | 50 | 0 | 5s | - | FAIL bcd2345",
            "omi-agent-reviewer | m-a | high | 1 | 1 | 1 | 5s | - | QUOTA->codex"])
        usage_task(root, "TASK-002", "PLAN-002", "codex", ["omi-agent-engineer | m-b (codex) | high | 10 | 20 | 30 | 5s | - | -"])
        write(root / ".omi/tasks/TASK-003.md", "---\nid: TASK-003\nstatus: planned\n---\n")
        remote(home)
        view = data.cost("sample")
        assert not view["has_prices"] and [t["id"] for t in view["tasks"]] == ["TASK-001", "TASK-002"]
        first = view["tasks"][0]
        assert (first["input"], first["output"], first["cache"], first["runs"]) == (1000201, 500101, 2000001, 4)
        assert (first["review_rounds"], first["fails"], first["top"], first["cost"]) == (2, 2, 1, None)
        assert [(p["plan"], p["runs"]) for p in view["plans"]] == [("PLAN-001", 4), ("PLAN-002", 1)]
        assert [(t["tool"], t["tokens"]) for t in view["tools"]] == [("claude", 3500303), ("codex", 60)]
        assert [m["model"] for m in view["models"]] == ["m-a", "m-b (codex)"] and view["totals"]["runs"] == 5
        assert view["totals"]["cost"] is None
        write(home / "projects/sample/.omi/config.json", json.dumps({"prices": {"m-a": {"input": 1, "output": 2, "cache": 0.5}}}))
        publish(home)
        view = data.cost("sample")
        assert view["has_prices"] and view["tasks"][0]["cost"] == 3.0004
        assert view["tasks"][1]["cost"] is None and view["totals"]["cost"] is None  # m-b has no price
        write(home / "projects/sample/.omi/config.json", "{bad")
        publish(home)
        assert not data.cost("sample")["has_prices"]


def test_cost_legacy_usage() -> None:
    # Usage tables copied from TASK-026 (7 columns) and TASK-035 (8 columns).
    tables = (
        """## Usage
| role | model | effort | input | output | cache | duration |
|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 22 | 9893 | 465579 | 92s |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 1461 | 93093 | 20s |
""",
        """## Usage
| role | model | effort | input | output | cache | duration | skills read |
|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 14 | 3061 | 150263 | 37s | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 12 | 1669 | 148530 | 35s | - |
"""
    )
    with state_dir() as directory:
        home = Path(directory)
        root = home / "projects/sample"
        for id, table in zip(("TASK-026", "TASK-035"), tables):
            write(root / f".omi/tasks/{id}.md", f"---\nid: {id}\nplan: PLAN-001\n---\n{table}\n")
        remote(home)
        view = data.cost("sample")
        by_task = {t["id"]: t for t in view["tasks"]}
        for id, expected in (("TASK-026", (28, 11354, 558672)), ("TASK-035", (26, 4730, 298793))):
            row = by_task[id]
            assert (row["input"], row["output"], row["cache"]) == expected
            assert (row["runs"], row["review_rounds"], row["fails"]) == (2, 1, 0)
        assert view["totals"]["runs"] == 4 and view["totals"]["review_rounds"] == 2
        assert view["plans"][0]["tokens"] == view["tools"][0]["tokens"] == view["models"][0]["tokens"] == 873603


def test_cost_mixed_tools_per_task() -> None:
    # All six Usage rows from TASK-125; frontmatter names only the current tool.
    table = """| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-designer-ui | gpt-6.1-sol (codex) | medium | 1879579 | 22644 | 1833600 | 482s | 2/2 omi-skill-ui-direction omi-skill-ui-a11y-review | - |
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 3131809 | 18765 | 3068288 | 661s | 2/2 omi-skill-ui-direction omi-skill-lean-implementation | - |
| omi-agent-qa-tester | claude-sonnet-5-5 | medium | 44 | 5362 | 667652 | 539s | - | PASS 684e44c |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 14 | 4327 | 352156 | 323s | - | FAIL 684e44c |
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 4791246 | 22961 | 4713600 | 306s | 0/2 | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 12 | 3495 | 302635 | 495s | - | PASS 6499fb8 |
"""
    with state_dir() as directory:
        home = Path(directory)
        root = home / "projects/sample"
        write(root / ".omi/tasks/TASK-125.md", "---\nid: TASK-125\nplan: PLAN-007\ntool: codex\n---\n## Usage\n" + table + "\n")
        remote(home)
        view = data.cost("sample")
        tools = {t["tool"]: t for t in view["tools"]}
        assert set(tools) == {"claude", "codex"}
        for tool, expected in (("claude", (70, 13184, 1322443, 2)),
                               ("codex", (9802634, 64370, 9615488, 0))):
            row = tools[tool]
            assert (row["input"], row["output"], row["cache"], row["review_rounds"]) == expected
            assert row["runs"] == 3
            assert row["tokens"] == sum(expected[:3])
            model = next(m for m in view["models"] if ("(codex)" in m["model"]) == (tool == "codex"))
            assert all(row[k] == model[k] for k in ("input", "output", "cache", "runs", "review_rounds", "tokens", "cost"))
        task = view["tasks"][0]
        assert (task["runs"], task["review_rounds"], task["fails"]) == (6, 2, 1)
        assert task["tool"] == "claude, codex"
        for key in ("input", "output", "cache", "runs", "tokens", "review_rounds"):
            assert task[key] == view["plans"][0][key] == view["totals"][key] == sum(t[key] for t in tools.values())
        assert not view["has_prices"] and view["totals"]["cost"] is None


def test_inbox_detection() -> None:
    base = {"id": "TASK-115", "status": "in-progress", "current_step": "accept",
            "frontmatter": {"title": "<script>task</script>"}, "workflow_steps": [{"id": "accept", "gate": "po"}],
            "steps": "- accept started 2026-11-01 12:00", "reports": "", "checkpoint": "", "usage": {"rows": []}}
    gate = data._inbox(base)
    assert gate == [{"id": "TASK-115", "title": "<script>task</script>", "reason": "po_gate", "gate": "accept",
                     "text": "Duyệt bước accept", "since": "2026-11-01 12:00", "command": "omi-task TASK-115"}]
    for event in ("done", "skipped"):
        assert not data._inbox({**base, "steps": base["steps"] + f"\n- accept {event} 2026-11-01 12:01"})
    assert not data._inbox({**base, "status": "done"})
    assert not data._inbox({**base, "steps": base["steps"] + "\nPO approval accept: Approved"})
    design = {**base, "current_step": "approve-mockup", "workflow_steps": [{"id": "approve-mockup", "gate": "po"}], "steps": ""}
    assert data._inbox(design)[0]["since"] is None
    worker = {**base, "current_step": "build", "steps": ""}
    for marker, reason in (("NEEDS SCOPE", "needs_scope"), ("QUOTA", "quota")):
        report = f"2026-11-01 12:00 omi-agent-engineer (codex):\n> {marker}: need PO decision"
        item = data._inbox({**worker, "reports": report})[0]
        assert item["reason"] == reason and item["since"] == "2026-11-01 12:00"
        assert data._inbox({**worker, "checkpoint": f"Next: {marker}: ask PO"})[0]["since"] is None
        assert not data._inbox({**worker, "reports": report + "\n2026-11-01 13:00 engineer:\n> DONE"})
        assert not data._inbox({**worker, "reports": report, "steps": "- build started 2026-11-01 13:00"})
    assert not data._inbox({**worker, "checkpoint": "QUOTA: tool hit limit; engineer continued with codex on partial diff."})
    assert not data._inbox({**worker, "reports": "2026-11-01 12:00 engineer:\n> historical QUOTA and NEEDS SCOPE are resolved"})
    assert not data._inbox({**worker, "checkpoint": "QUOTA: stopped; resume required",
                            "usage": {"rows": [{"role": "omi-agent-engineer", "verdict": "-"}]}})
    rows = [{"role": "omi-agent-reviewer", "verdict": "FAIL abc1234"}] * 2
    review = {**worker, "usage": {"rows": rows}, "reports": "2026-11-01 12:00 Coordinator (review) FAIL:\n> Waiting for PO decision"}
    assert data._inbox(review)[0]["reason"] == "review_fail"
    assert not data._inbox({**review, "usage": {"rows": rows[:1]}})
    assert not data._inbox({**review, "reports": "2026-11-01 13:00 engineer:\n> DONE"})
    assert not data._inbox({**review, "usage": {"rows": rows + [{"role": "omi-agent-reviewer", "verdict": "PASS def5678"}]}})
    # Excerpts from TASK-123 / TASK-126: reports stop without an explicit PO request.
    real_reports = [
        "2026-11-01 08:07 omi-agent-reviewer (claude):\n"
        "> The verdict is unchanged: FAIL, on AC5 only. No mockup-comparison evidence is recorded, and the review rules don't allow PASS without it.",
        "2026-11-01 15:30 omi-agent-reviewer (claude):\n> ```\n> VERDICT: FAIL\n> ```",
        "2026-11-01 07:48 Coordinator (review) FAIL:\n> Fix round 1: re-focus the matching new node; 2 s TTL kept (about 3 s criterion, shared cache); mockup comparison left to qa; Host wheel test ok.",
    ]
    for report in real_reports:
        stopped = {**review, "reports": report}
        assert data._inbox(stopped)[0]["reason"] == "review_fail"
        assert not data._inbox({**stopped, "usage": {"rows": rows[:1]}})
        assert not data._inbox({**stopped, "steps": "- build started 2026-11-01 16:00"})
        assert not data._inbox({**stopped, "reports": report + "\n2026-11-01 16:00 engineer:\n> DONE"})
    for note in (
        '2026-11-01 09:17 Coordinator (review) FAIL:\n> Round 2 FAIL on mockup evidence only. PO: "Chạy QA trước, rồi review lại". QA runs now, then review round 3.',
        '2026-11-01 15:45 Coordinator (review) FAIL:\n> Round 4 FAIL: host wheel ok on 837e481; row tool from frontmatter. PO: "Sửa nốt điểm 2 rồi merge".',
    ):
        assert not data._inbox({**review, "reports": note})
    for marker in ("NEEDS SCOPE", "QUOTA"):
        pending = {**worker, "checkpoint": f"Next: {marker}: ask PO"}
        first = data._inbox(pending)[0]
        repeated = data._inbox({**pending, "usage": {"rows": [{"role": "omi-agent-engineer", "verdict": "QUOTA->codex"}]}})[0]
        assert first["since"] is repeated["since"] is None
        assert first["request_marker"] == repeated["request_marker"]
        report = f"2026-11-01 12:00 engineer:\n> {marker}: ask PO"
        assert data._inbox({**worker, "reports": report})[0]["request_marker"] != data._inbox(
            {**worker, "reports": report.replace("12:00", "13:00")})[0]["request_marker"]
        # pending -> resolved -> raised again: same marker while pending, new one on re-raise.
        marks = []
        for state in ({"reports": report}, {"reports": report + "\n2026-11-01 12:30 hook x:\n> ok"}, {},
                      {"reports": report.replace("12:00", "14:00")}):
            items = data._inbox({**worker, **state})
            marks.append(items[0]["request_marker"] if items else None)
        assert marks[0] == marks[1] and marks[2] is None and marks[3] != marks[0]
        marks = []
        for state in ({"checkpoint": f"Next: {marker}: ask PO"}, {"checkpoint": f"Next: {marker}: ask PO",
                       "reports": "2026-11-01 12:30 engineer:\n> still working"},
                      {"checkpoint": "Next: continued"}, {"checkpoint": f"Next: {marker}: ask again"}):
            items = data._inbox({**worker, **state})
            marks.append(items[0]["request_marker"] if items else None)
        assert marks[0] == marks[1] and marks[2] is None and marks[3] != marks[0]
    combined = data._inbox({**base, "checkpoint": "Next: NEEDS SCOPE: add a file\nQUOTA: resume required"})
    assert {i["reason"] for i in combined} == {"po_gate", "needs_scope", "quota"}


def test_inbox_aggregation() -> None:
    with state_dir() as directory:
        home = Path(directory)
        fixture(home)
        for project, stamp in (("other", "2026-10-28 12:00"), ("sample", "2026-10-29 12:00")):
            root = home / "projects" / project
            write(root / ".omi/workflows/feature.md", "---\nsteps:\n- id: accept | gate: po\n---\n")
            write(root / ".omi/tasks/TASK-002.md", "---\nid: TASK-002\nstatus: in-progress\nworkflow: feature\nstep: accept\n---\n## Steps\n- accept started " + stamp + "\n")
        remote(home)
        before = {f: f.read_bytes() for f in (home / "projects").rglob("*.md")}
        inbox = data.projects()["inbox"]
        assert [(i["project"], i["id"], i["since"]) for i in inbox] == [
            ("other", "TASK-002", "2026-10-28 12:00"), ("sample", "TASK-002", "2026-10-29 12:00")]
        assert before == {f: f.read_bytes() for f in before}


STEPS = """- plan started 2026-11-02 16:29
- plan done 2026-11-02 16:29
- approve started 2026-11-02 16:30
PO approval approve: ok
- approve done 2026-11-02 16:32:03
- build started 2026-11-02 16:41
- build done 2026-11-02 17:46
- review started 2026-11-02 17:46
- review done 2026-11-02 18:11
Auto accept: review PASS
- qa started 2026-11-02 18:11"""
REPORTS = """2026-11-02 17:40 omi-agent-engineer (claude):
> DONE
> Tests ok
2026-11-02 17:41 hook post-run passed:
> ok
2026-11-02 18:01 omi-agent-reviewer (claude):
> FAIL
> file:line - bug
2026-11-02 18:10 omi-agent-reviewer (claude):
> VERDICT: PASS
2026-11-01 10:00 omi-agent-designer-ui (claude):
> BLOCKED needs input"""


def test_timeline() -> None:
    assert [timeline.duration(s) for s in (0, 59, 61, 3600, 3723, 7200 + 59)] == ["0 giây", "59 giây", "1 phút 1 giây", "1 giờ", "1 giờ 2 phút", "2 giờ"]
    t = timeline.build(STEPS, REPORTS, data.datetime(2026, 11, 2, 18, 23, 40))
    rows = t["rows"]
    assert [r.get("name", r.get("text")) for r in rows] == ["plan", "approve", "PO approval approve: ok", "build", "review", "Auto accept: review PASS", "qa"]
    by = {r["name"]: r for r in rows if r["kind"] == "step"}
    assert by["plan"]["duration"] == "0 giây" and by["approve"]["duration"] == "2 phút 3 giây" and by["approve"]["po"] and not by["plan"]["po"]
    assert by["build"]["duration"] == "1 giờ 5 phút" and by["build"]["percent"] == 100
    assert by["qa"]["state"] == "running" and by["qa"]["duration"] == "12 phút 40 giây" and t["now"] == "18:23"
    note = next(r for r in rows if r.get("text") == "Auto accept: review PASS")
    assert note["kind"] == "note" and note["start"] == "2026-11-02 18:11"
    assert [(x["n"], x["role"], x["verdict"], x["open"]) for x in by["build"]["rounds"]] == [(1, "engineer", "DONE", False)]
    assert [(x["n"], x["verdict"], x["open"]) for x in by["review"]["rounds"]] == [(1, "FAIL", True), (2, "PASS", False)]
    assert by["review"]["fail"] and not by["build"]["fail"] and by["review"]["rounds"][0]["body"] == "FAIL\nfile:line - bug"
    assert t["summary"]["steps"] == 5 and t["summary"]["running"] == 1 and t["summary"]["rounds"] == 3 and t["summary"]["fails"] == 1
    empty = timeline.build("", "", data.datetime(2026, 11, 2))
    assert empty["rows"] == [] and empty["summary"]["steps"] == 0


def test_task_detail_files() -> None:
    text = "---\nid: TASK-001\nfiles: src/a.py, tests/b.py\n---\n## Steps\n- build started 2026-11-02 16:00\n"
    snap = type("S", (), {"paths": set()})()
    detail = data._detail(snap, Path("p"), "TASK-001", text)
    assert detail["files"] == ["src/a.py", "tests/b.py"] and detail["timeline"]["rows"][0]["name"] == "build"
    assert data._detail(snap, Path("p"), "TASK-001", text.replace("files: src/a.py, tests/b.py\n", ""))["files"] == []


def test_alerts() -> None:
    row = {"role": "omi-agent-reviewer", "verdict": "FAIL abc1234"}

    def task(id, status="in-progress", steps="- build started 2026-11-01 12:00", rows=(), **meta):
        return {"id": id, "status": status, "steps": steps, "reports": "", "usage": {"rows": list(rows)},
                "frontmatter": {"title": "t", **meta}}

    details = [task("TASK-001"), task("TASK-002", rows=[row, row]), task("TASK-003", behind="21"), task("TASK-004", behind="20"),
               task("TASK-005", "blocked"), task("TASK-006", "planned", depends="TASK-005"), task("TASK-007", rows=[row]),
               task("TASK-008", "done", rows=[row, row]), task("TASK-009", "planned", steps="- x started 2020-01-01 00:00")]
    with patch.object(data, "_now", lambda: data.datetime(2026, 11, 4, 11, 0)):  # 2d23h after the stamp
        assert {a["id"] for a in data._alerts(details, 3)} == {"TASK-002", "TASK-003", "TASK-006"}
        stale = data._alerts(details, 2)
        assert [a["kind"] for a in stale if a["id"] == "TASK-001"] == ["stale"] and "ngưỡng: 2 ngày" in stale[0]["reason"]
    kinds = {a["id"]: a["kind"] for a in data._alerts(details, 3)}
    assert kinds["TASK-002"] == "review_fail" and kinds["TASK-003"] == "behind" and kinds["TASK-006"] == "blocked_dep"
    assert next(a for a in data._alerts(details, 3) if a["id"] == "TASK-002")["chip"] == "Review FAIL ×2"
    assert data._alerts([task("TASK-010", steps="")], 3) == []


def test_alerts_config() -> None:
    with state_dir() as directory:
        home = Path(directory)
        root = fixture(home)
        remote(home)
        now = data.datetime(2026, 11, 2, 12, 0)  # TASK-002 last stamp: 2026-10-29 13:00, 3d23h ago
        with patch.object(data, "_now", lambda: now):
            view = data.project("sample")
            assert [(a["id"], a["kind"]) for a in view["alerts"]] == [("TASK-002", "stale"), ("TASK-005", "blocked_dep")]
            assert "ngưỡng: 3 ngày" in view["alerts"][0]["reason"]
            write(root / ".omi/config.json", json.dumps({"board_stale_days": 5}))
            publish(home)
            assert [a["kind"] for a in data.project("sample")["alerts"]] == ["blocked_dep"]
            write(root / ".omi/config.json", "{bad")
            publish(home)
            assert [a["kind"] for a in data.project("sample")["alerts"]] == ["stale", "blocked_dep"]
        assert data.projects()["projects"][0]["name"] == "sample"


def graph_items(*specs):
    return [{"id": id, "status": status, "frontmatter": {"title": id.lower(), "depends": depends, "plan": plan}}
            for id, status, depends, plan in specs]


def test_graph_layers_and_critical_path() -> None:
    g = data._graph(graph_items(("A", "done", "", "P"), ("B", "done", "A", "P"), ("C", "blocked", "A, B", "P"),
                                ("D", "planned", "C, B", "P"), ("E", "planned", "B", "P"), ("F", "planned", "", "P")))
    assert {n["id"]: n["layer"] for n in g["nodes"]} == {"A": 1, "F": 1, "B": 2, "C": 3, "E": 3, "D": 4}
    assert g["critical_path"] == ["A", "B", "C", "D"] and not g["cycles"] and not g["empty"]
    assert [(e["from"], e["to"]) for e in g["edges"] if e["critical"]] == [("A", "B"), ("B", "C"), ("C", "D")]
    c, d = (next(n for n in g["nodes"] if n["id"] == i) for i in "CD")
    assert c["blocked_by"] == [] and c["blocks"] == ["D"] and d["waiting"] == ["C"] and d["critical"]
    assert g["summary"] == {"tasks": 6, "layers": 4, "blocked": 1, "critical_left": 2, "critical": 4, "cycle_tasks": 0}
    assert data._graph(graph_items(("A", "planned", "", ""), ("B", "planned", "", "")))["empty"]
    # Dependencies outside the scope (another plan, unknown ids) do not create edges.
    assert data._graph(graph_items(("A", "planned", "OTHER-1", "")))["empty"]


def test_graph_cycles() -> None:
    g = data._graph(graph_items(("A", "planned", "", ""), ("X", "planned", "Z, A", ""), ("Y", "planned", "X", ""),
                                ("Z", "planned", "Y", ""), ("S", "planned", "S", ""), ("T", "planned", "Z", "")))
    assert g["cycles"] == [["S", "S"], ["X", "Y", "Z", "X"]]
    assert [n["id"] for n in g["nodes"]] == ["A", "T"] and g["summary"]["cycle_tasks"] == 4
    assert g["nodes"][1]["layer"] == 1 and not g["empty"]


def test_graph_view() -> None:
    with state_dir() as directory:
        home = Path(directory)
        fixture(home)
        remote(home)
        view = data.graph("sample")
        assert view["plans"] == [{"id": "PLAN-001", "title": "Plan", "status": "active"}]
        assert set(view["scopes"]) == {"all", "PLAN-001"} and view["scopes"]["all"] == view["scopes"]["PLAN-001"]
        graph = view["scopes"]["all"]
        assert [(e["from"], e["to"]) for e in graph["edges"]] == [("TASK-001", "TASK-004"), ("TASK-003", "TASK-005")]
        assert graph["summary"]["blocked"] == 1 and graph["critical_path"] == ["TASK-001", "TASK-004"]
        assert next(n for n in graph["nodes"] if n["id"] == "TASK-005")["waiting"] == ["TASK-003"]


def main():
    test_inbox_detection()
    test_inbox_aggregation()
    test_views()
    test_plan_status_derived()
    test_hierarchy()
    test_shared_fetch()
    test_version()
    test_path_redaction()
    test_unavailable_snapshot()
    test_fetch_timeout_serves_stale()
    test_workflow_detail()
    test_path_refusal()
    test_snapshot_symlink_unavailable()
    test_empty_and_layer()
    test_snapshot_one_git_process()
    test_snapshot_load_hardened()
    test_newline_path_skipped()
    test_request_does_not_wait_for_fetch()
    test_projects_cached_per_commit_and_minute()
    test_cost()
    test_cost_legacy_usage()
    test_cost_mixed_tools_per_task()
    test_timeline()
    test_task_detail_files()
    test_alerts()
    test_alerts_config()
    test_graph_layers_and_critical_path()
    test_graph_cycles()
    test_graph_view()


if __name__ == "__main__":
    main()
