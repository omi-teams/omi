"""Board data contracts, read-only behavior and state path boundaries."""
import json
import os
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import helpers
from helpers import git
from omi.board import data, source


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


def publish(home):
    git(home, "add", ".")
    git(home, "commit", "-qm", "state update")
    git(home, "push", "-q", "origin", "main")
    source._CACHE.clear()


def test_views():
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OMI_STATE": directory}):
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
        pushed = data.task("sample", "TASK-002")
        assert pushed["goal"] == "Pushed elsewhere" and pushed["source"]["sha"] != old_sha
        # Neither successful nor failed fetch alters HEAD, index or local files.
        write(path, "local dirty data")
        head = data.core.git(home, "rev-parse", "HEAD")
        status = data.core.git(home, "status", "--porcelain")
        with patch("omi.board.source.time.monotonic", return_value=source._CACHE[home][0] + 11):
            assert data.task("sample", "TASK-002")["goal"] == pushed["goal"]
        assert path.read_text(encoding="utf-8") == "local dirty data"
        assert data.core.git(home, "rev-parse", "HEAD") == head
        assert data.core.git(home, "status", "--porcelain") == status
        pushed = data.task("sample", "TASK-002")
        git(home, "remote", "set-url", "origin", str(origin / "unavailable"))
        with patch("omi.board.source.time.monotonic", return_value=source._CACHE[home][0] + 11):
            stale = data.task("sample", "TASK-002")
        assert stale["goal"] == pushed["goal"]
        assert stale["source"]["stale"] is True
        assert stale["source"]["fetched_at"] == pushed["source"]["fetched_at"]
        assert stale["source"]["sha"] == pushed["source"]["sha"]
        assert path.read_text(encoding="utf-8") == "local dirty data"
        assert data.core.git(home, "rev-parse", "HEAD") == head
        assert data.core.git(home, "status", "--porcelain") == status
        git(home, "remote", "set-url", "origin", str(origin))
        with patch("omi.board.source.time.monotonic", return_value=source._CACHE[home][0] + 11):
            assert data.task("sample", "TASK-002")["source"]["stale"] is False


def test_plan_status_derived():
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OMI_STATE": directory}):
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
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OMI_STATE": directory}):
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
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OMI_STATE": directory}):
        home = Path(directory)
        fixture(home)
        remote(home)
        real_git, real_fetch = source.core.git, source._fetch
        with patch("omi.board.source.core.git", wraps=real_git) as calls, patch("omi.board.source._fetch", wraps=real_fetch) as fetches, \
                patch("omi.board.source.time.monotonic", return_value=100):
            with ThreadPoolExecutor(max_workers=6) as pool:
                views = list(pool.map(lambda _: data.projects(), range(12)))
            assert all(v["source"] == views[0]["source"] for v in views)
            assert fetches.call_count == 1
            with patch("omi.board.source.time.monotonic", return_value=101):
                data.projects()
            assert fetches.call_count == 1
            with patch("omi.board.source.time.monotonic", return_value=102):
                data.projects()
            assert fetches.call_count == 2
            assert {c.args[1] for c in calls.call_args_list} <= {"rev-parse", "remote", "ls-tree", "show"}
        for url, expected in (("https://user:token@github.com/omi-teams/omi-state?token=secret", "https://github.com/omi-teams/omi-state"),
                              ("git@github.com:omi-teams/omi-state.git", "github.com:omi-teams/omi-state.git"),
                              ("ssh://git@github.com:2222/omi-teams/omi-state.git", "ssh://github.com:2222/omi-teams/omi-state.git"),
                              (str(home), ""), (r"C:\x\y", ""), ("C:/x/y", ""), ("file:///local/state", "")):
            assert source._repo(url) == expected


def test_version() -> None:
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OMI_STATE": directory}):
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
    with tempfile.TemporaryDirectory() as directory:
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


def test_unavailable_snapshot():
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OMI_STATE": directory}):
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
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OMI_STATE": directory}):
        home = Path(directory)
        fixture(home)
        remote(home)
        fresh = data.projects()["source"]
        seen, real_run = [], subprocess.run

        def hang(argv, **kw):  # only the fetch hangs; other git calls still read the cache
            if "fetch" not in argv:
                return real_run(argv, **kw)
            seen.append((argv, kw))
            raise subprocess.TimeoutExpired(argv, kw["timeout"])
        with patch("omi.board.source.subprocess.run", side_effect=hang), \
                patch("omi.board.source.time.monotonic", return_value=source._CACHE[home][0] + 11):
            stale = data.projects()["source"]
        (argv, kw), = seen
        assert "fetch" in argv and kw["env"]["GIT_TERMINAL_PROMPT"] == "0" and kw["timeout"] == source.FETCH_TIMEOUT
        assert kw["env"]["GCM_INTERACTIVE"] == "never" and kw["stdout"] == kw["stderr"] == subprocess.DEVNULL and "capture_output" not in kw
        assert stale["stale"] is True and stale["sha"] == fresh["sha"] and stale["fetched_at"] == fresh["fetched_at"]


def test_workflow_detail():
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OMI_STATE": directory}):
        root = fixture(Path(directory))
        steps = [{"id": id, "gate": "po" if id == "accept" else "none"}
                 for id in ("plan", "design", "build", "review", "accept", "qa")]
        definition = "---\nsteps:\n" + "".join(f"- id: {s['id']} | gate: {s['gate']}\n" for s in steps) + "---\n"
        write(root / ".omi/workflows/feature.md", definition)
        remote(Path(directory))
        detail = data.task("sample", "TASK-002")
        assert detail["workflow_steps"] == steps and detail["current_step"] == "accept"
        assert data.project("sample")["kanban"]["in-progress"][0] == {k: v for k, v in detail.items() if k != "source"}
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
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OMI_STATE": directory}):
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
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OMI_STATE": directory}):
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
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OMI_STATE": directory}):
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
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OMI_STATE": directory}):
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
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OMI_STATE": directory}):
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
        assert first["request_marker"] != repeated["request_marker"]
        report = f"2026-11-01 12:00 engineer:\n> {marker}: ask PO"
        assert data._inbox({**worker, "reports": report})[0]["request_marker"] != data._inbox(
            {**worker, "reports": report.replace("12:00", "13:00")})[0]["request_marker"]
    combined = data._inbox({**base, "checkpoint": "Next: NEEDS SCOPE: add a file\nQUOTA: resume required"})
    assert {i["reason"] for i in combined} == {"po_gate", "needs_scope", "quota"}


def test_inbox_aggregation() -> None:
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OMI_STATE": directory}):
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
    test_cost()
    test_cost_legacy_usage()
    test_cost_mixed_tools_per_task()


if __name__ == "__main__":
    main()
