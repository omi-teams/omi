"""Board data contracts, read-only behavior and state path boundaries."""
import json
import os
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


def test_shared_fetch():
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OMI_STATE": directory}):
        home = Path(directory)
        fixture(home)
        remote(home)
        real_git = source.core.git
        with patch("omi.board.source.core.git", wraps=real_git) as calls, patch("omi.board.source.time.monotonic", return_value=100):
            with ThreadPoolExecutor(max_workers=6) as pool:
                views = list(pool.map(lambda _: data.projects(), range(12)))
            assert all(v["source"] == views[0]["source"] for v in views)
            assert sum(c.args[1] == "fetch" for c in calls.call_args_list) == 1
            with patch("omi.board.source.time.monotonic", return_value=109):
                data.projects()
            assert sum(c.args[1] == "fetch" for c in calls.call_args_list) == 1
            with patch("omi.board.source.time.monotonic", return_value=110):
                data.projects()
            assert sum(c.args[1] == "fetch" for c in calls.call_args_list) == 2
            assert {c.args[1] for c in calls.call_args_list} <= {"fetch", "rev-parse", "remote", "ls-tree", "show"}
        for url, expected in (("https://user:token@github.com/omi-teams/omi-state?token=secret", "https://github.com/omi-teams/omi-state"),
                              ("git@github.com:omi-teams/omi-state.git", "github.com:omi-teams/omi-state.git"),
                              ("ssh://git@github.com:2222/omi-teams/omi-state.git", "ssh://github.com:2222/omi-teams/omi-state.git"),
                              (str(home), ""), (r"C:\x\y", ""), ("C:/x/y", ""), ("file:///local/state", "")):
            assert source._repo(url) == expected


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
        with patch("omi.board.source.core.git", return_value=None) as calls, patch("omi.board.source.time.monotonic", return_value=100):
            for _ in range(2):
                try:
                    data.projects()
                except OSError as exc:
                    assert str(Path(directory)) not in str(exc)
                else:
                    raise AssertionError("missing origin/main served local content")
            assert sum(c.args[1] == "fetch" for c in calls.call_args_list) == 1


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
    rule = (Path(__file__).parents[1] / ".omi/rules/omi-modules.md").read_text(encoding="utf-8")
    order = next(line for line in rule.splitlines() if "module layer order" in line)
    assert order.index("app.cli") < order.index("board.data") < order.index("board.source") < order.index("project.tasks") < order.index("state.resolve")


def main():
    test_views()
    test_shared_fetch()
    test_path_redaction()
    test_unavailable_snapshot()
    test_workflow_detail()
    test_path_refusal()
    test_snapshot_symlink_unavailable()
    test_empty_and_layer()


if __name__ == "__main__":
    main()
